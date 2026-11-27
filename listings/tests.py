from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .forms import TicketForm
from .models import Property, Ticket


class PropertyModelTests(TestCase):
    def test_valid_residential_sale_combination(self):
        prop = Property(
            title="آپارتمان نمونه",
            deal_type=Property.DEAL_SALE,
            usage_type=Property.USAGE_RESIDENTIAL,
            property_type=Property.PT_APARTMENT,
        )
        prop.full_clean()

    def test_invalid_property_category_combination_is_rejected(self):
        prop = Property(
            title="دفتر اداری",
            deal_type=Property.DEAL_RENT,
            usage_type=Property.USAGE_RESIDENTIAL,
            property_type=Property.PT_OFFICE,
        )
        with self.assertRaises(ValidationError):
            prop.full_clean()


class PropertyListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for index in range(13):
            Property.objects.create(
                title=f"ملک آزمایشی {index}",
                deal_type=Property.DEAL_SALE,
                usage_type=Property.USAGE_RESIDENTIAL,
                property_type=Property.PT_APARTMENT,
                city="تهران" if index < 4 else "کرج",
                area=80 + index,
                status=Property.STATUS_ACTIVE,
            )

        Property.objects.create(
            title="ملک فروخته‌شده",
            deal_type=Property.DEAL_SALE,
            usage_type=Property.USAGE_RESIDENTIAL,
            property_type=Property.PT_APARTMENT,
            city="تهران",
            area=100,
            status=Property.STATUS_SOLD,
        )

    def test_only_active_properties_are_listed(self):
        response = self.client.get(reverse("listings:list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["count"], 13)
        self.assertNotContains(response, "ملک فروخته‌شده")

    def test_listing_is_paginated(self):
        response = self.client.get(reverse("listings:list"), {"page": "2"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 2)
        self.assertEqual(len(response.context["properties"]), 1)

    def test_area_and_city_filters_can_be_combined(self):
        response = self.client.get(
            reverse("listings:list"),
            {"city": "تهران", "min_area": "82", "max_area": "84"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["count"], 2)


class TicketFormTests(TestCase):
    def test_valid_ticket_is_saved(self):
        response = self.client.post(
            reverse("listings:contact"),
            {
                "name": "کاربر آزمایشی",
                "phone": "09120000000",
                "email": "test@example.com",
                "subject": "درخواست اطلاعات",
                "message": "لطفاً با من تماس بگیرید.",
                "website": "",
            },
        )
        self.assertRedirects(response, reverse("listings:contact"))
        self.assertEqual(Ticket.objects.count(), 1)

    def test_invalid_email_is_rejected(self):
        form = TicketForm(
            data={
                "name": "کاربر آزمایشی",
                "phone": "09120000000",
                "email": "not-an-email",
                "subject": "موضوع",
                "message": "پیام",
                "website": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_honeypot_submission_is_discarded(self):
        response = self.client.post(
            reverse("listings:contact"),
            {
                "name": "Bot",
                "phone": "000",
                "email": "",
                "subject": "Spam",
                "message": "Spam",
                "website": "filled-by-bot",
            },
        )
        self.assertRedirects(response, reverse("listings:contact"))
        self.assertEqual(Ticket.objects.count(), 0)
