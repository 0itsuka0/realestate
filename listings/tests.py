from django.contrib.auth.models import Permission, User
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



class ManagerAdminTests(TestCase):
    def setUp(self):
        self.root = User.objects.create_superuser(
            username="rootadmin",
            email="root@example.com",
            password="Root-Test-Password-2026!",
        )
        self.client.force_login(self.root)

    def test_manager_add_form_only_shows_login_and_section_checkboxes(self):
        response = self.client.get(reverse("admin:auth_user_add"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password1"')
        self.assertContains(response, 'name="password2"')
        self.assertContains(response, 'name="can_manage_properties"')
        self.assertContains(response, 'name="can_manage_contact"')
        self.assertNotContains(response, 'name="email"')
        self.assertNotContains(response, 'name="first_name"')
        self.assertNotContains(response, 'name="groups"')
        self.assertNotContains(response, 'name="user_permissions"')
        self.assertNotContains(response, 'name="is_superuser"')

    def test_create_manager_assigns_only_selected_section_permissions(self):
        response = self.client.post(
            reverse("admin:auth_user_add"),
            {
                "username": "propertymanager",
                "password1": "Unique-Manager-Password-2026!",
                "password2": "Unique-Manager-Password-2026!",
                "can_manage_properties": "on",
            },
        )
        self.assertEqual(response.status_code, 302)

        manager = User.objects.get(username="propertymanager")
        self.assertTrue(manager.is_staff)
        self.assertTrue(manager.is_active)
        self.assertFalse(manager.is_superuser)
        self.assertTrue(manager.has_perm("listings.view_property"))
        self.assertTrue(manager.has_perm("listings.add_propertyimage"))
        self.assertTrue(manager.has_perm("listings.change_propertyvideo"))
        self.assertFalse(manager.has_perm("listings.view_ticket"))
        self.assertFalse(manager.groups.exists())

    def test_editing_manager_replaces_permissions_from_checkboxes(self):
        manager = User.objects.create_user(
            username="editablemanager",
            password="Existing-Manager-Password-2026!",
            is_staff=True,
        )
        property_permission = Permission.objects.get_by_natural_key(
            "view_property", "listings", "property"
        )
        manager.user_permissions.add(property_permission)

        response = self.client.post(
            reverse("admin:auth_user_change", args=[manager.pk]),
            {
                "username": "editablemanager",
                "can_manage_tickets": "on",
            },
        )
        self.assertEqual(response.status_code, 302)

        manager.refresh_from_db()
        self.assertTrue(manager.has_perm("listings.view_ticket"))
        self.assertTrue(manager.has_perm("listings.change_ticket"))
        self.assertFalse(manager.has_perm("listings.view_property"))

    def test_manager_can_be_deleted_from_manager_list(self):
        manager = User.objects.create_user(
            username="deleteme",
            password="Delete-Manager-Password-2026!",
            is_staff=True,
        )
        response = self.client.post(
            reverse("admin:auth_user_delete", args=[manager.pk]),
            {"post": "yes"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=manager.pk).exists())

    def test_superuser_is_not_listed_as_a_manager(self):
        response = self.client.get(reverse("admin:auth_user_changelist"))
        self.assertEqual(response.status_code, 200)
        listed_usernames = [
            user.username for user in response.context["cl"].result_list
        ]
        self.assertNotIn("rootadmin", listed_usernames)

    def test_manager_permissions_control_direct_admin_urls_and_menu(self):
        manager = User.objects.create_user(
            username="limitedmanager",
            password="Limited-Manager-Password-2026!",
            is_staff=True,
        )
        property_permissions = Permission.objects.filter(
            content_type__app_label="listings",
            content_type__model="property",
        )
        manager.user_permissions.add(*property_permissions)

        self.client.force_login(manager)
        allowed = self.client.get(reverse("admin:listings_property_changelist"))
        denied = self.client.get(reverse("admin:listings_ticket_changelist"))
        user_admin_denied = self.client.get(reverse("admin:auth_user_changelist"))
        index = self.client.get(reverse("admin:index"))

        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(user_admin_denied.status_code, 403)
        self.assertContains(index, "فایل‌های ملکی")
        self.assertNotContains(index, "تیکت‌ها")
        self.assertNotContains(index, "مدیریت مدیران")
