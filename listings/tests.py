from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .forms import TicketForm
from .models import ContactItem, Property, PropertyImage, PropertyVideo, SiteSettings, SocialLink, Ticket


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

    def test_homepage_has_right_sidebar_and_four_collapsed_search_groups(self):
        response = self.client.get(reverse("listings:list"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('class="property-page-layout"', content)
        self.assertIn('home-main-container', content)
        self.assertIn('class="property-search-sidebar"', content)
        self.assertEqual(content.count('<details class="search-accordion-section'), 4)
        detail_tags = [part.split(">", 1)[0] for part in content.split("<details")[1:]]
        self.assertTrue(all(" open" not in tag for tag in detail_tags))

    def test_homepage_uses_two_column_horizontal_property_card_grid(self):
        Property.objects.create(
            title="فایل با کارت افقی",
            deal_type=Property.DEAL_SALE,
            usage_type=Property.USAGE_RESIDENTIAL,
            property_type=Property.PT_APARTMENT,
            status=Property.STATUS_ACTIVE,
        )
        response = self.client.get(reverse("listings:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="property-grid"')
        self.assertContains(response, 'class="property-card property-card-horizontal"')
        self.assertContains(response, 'class="property-cover-wrap"')

    def test_admin_configured_homepage_banner_image_is_rendered_before_search(self):
        SiteSettings.objects.update_or_create(
            pk=1,
            defaults={
                "site_name": "املاک آزمایشی",
                "banner_image": "site/banners/home-test.jpg",
                "banner_title": "بنر آزمایشی",
                "banner_subtitle": "زیرعنوان بنر",
            },
        )
        response = self.client.get(reverse("listings:list"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('src="/media/site/banners/home-test.jpg"', content)
        self.assertLess(content.index('class="home-banner"'), content.index('class="property-search-panel"'))

    def test_listing_is_paginated(self):
        response = self.client.get(reverse("listings:list"), {"page": "2"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 2)
        self.assertEqual(len(response.context["properties"]), 1)
    def test_property_prices_use_persian_digits_and_three_digit_grouping(self):
        Property.objects.create(
            title="ملک فروشی با قیمت نمونه",
            deal_type=Property.DEAL_SALE,
            usage_type=Property.USAGE_RESIDENTIAL,
            property_type=Property.PT_APARTMENT,
            price=1_234_567_890,
            price_per_meter=12_345_678,
            status=Property.STATUS_ACTIVE,
        )
        Property.objects.create(
            title="ملک اجاره‌ای با قیمت نمونه",
            deal_type=Property.DEAL_RENT,
            usage_type=Property.USAGE_RESIDENTIAL,
            property_type=Property.PT_APARTMENT,
            deposit=987_654_321,
            rent=45_678_900,
            status=Property.STATUS_ACTIVE,
        )

        response = self.client.get(reverse("listings:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "۱٬۲۳۴٬۵۶۷٬۸۹۰")
        self.assertContains(response, "۱۲٬۳۴۵٬۶۷۸")
        self.assertContains(response, "۹۸۷٬۶۵۴٬۳۲۱")
        self.assertContains(response, "۴۵٬۶۷۸٬۹۰۰")
        self.assertContains(response, "تومان")

    def test_area_and_city_filters_can_be_combined(self):
        response = self.client.get(
            reverse("listings:list"),
            {"city": "تهران", "min_area": "82", "max_area": "84"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["count"], 2)


class AdvancedPropertySearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Property.objects.create(
            title="آپارتمان مدرن زعفرانیه",
            deal_type=Property.DEAL_SALE,
            usage_type=Property.USAGE_RESIDENTIAL,
            property_type=Property.PT_APARTMENT,
            province="تهران",
            city="تهران",
            neighborhood="زعفرانیه",
            price=4_000_000_000,
            bedrooms=3,
            has_parking=True,
            has_elevator=True,
            status=Property.STATUS_ACTIVE,
        )
        Property.objects.create(
            title="آپارتمان اقتصادی",
            deal_type=Property.DEAL_SALE,
            usage_type=Property.USAGE_RESIDENTIAL,
            property_type=Property.PT_APARTMENT,
            province="البرز",
            city="کرج",
            neighborhood="گوهردشت",
            price=2_000_000_000,
            bedrooms=2,
            status=Property.STATUS_ACTIVE,
        )
        Property.objects.create(
            title="واحد اجاره‌ای مرکز شهر",
            deal_type=Property.DEAL_RENT,
            usage_type=Property.USAGE_RESIDENTIAL,
            property_type=Property.PT_APARTMENT,
            province="تهران",
            city="تهران",
            neighborhood="مرکز شهر",
            deposit=500_000_000,
            rent=15_000_000,
            bedrooms=2,
            has_storage=True,
            status=Property.STATUS_ACTIVE,
        )
        Property.objects.create(
            title="واحد اجاره‌ای با ودیعه کمتر",
            deal_type=Property.DEAL_RENT,
            usage_type=Property.USAGE_RESIDENTIAL,
            property_type=Property.PT_APARTMENT,
            province="تهران",
            city="تهران",
            neighborhood="نارمک",
            deposit=250_000_000,
            rent=20_000_000,
            bedrooms=1,
            status=Property.STATUS_ACTIVE,
        )

    def test_sale_price_range_filters_total_sale_price(self):
        response = self.client.get(
            reverse("listings:list"),
            {"deal_type": "sale", "price_min": "3,000,000,000", "price_max": "5,000,000,000"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["count"], 1)
        self.assertContains(response, "آپارتمان مدرن زعفرانیه")

    def test_rent_filters_deposit_and_monthly_rent_separately(self):
        response = self.client.get(
            reverse("listings:list"),
            {
                "deal_type": "rent",
                "deposit_min": "400000000",
                "rent_max": "16000000",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["count"], 1)
        self.assertContains(response, "واحد اجاره‌ای مرکز شهر")

    def test_search_matches_multiple_words_across_location_fields(self):
        response = self.client.get(
            reverse("listings:list"),
            {"q": "تهران زعفرانیه"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["count"], 1)
        self.assertContains(response, "آپارتمان مدرن زعفرانیه")

    def test_bedroom_and_amenity_filters_can_be_combined(self):
        response = self.client.get(
            reverse("listings:list"),
            {"bedrooms": "3", "has_parking": "1", "has_elevator": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["count"], 1)

    def test_invalid_numeric_values_are_ignored_safely(self):
        response = self.client.get(
            reverse("listings:list"),
            {"deal_type": "sale", "price_min": "not-a-number"},
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
                "is_superuser": "on",
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

    def test_view_only_session_access_does_not_offer_delete_action(self):
        manager = User.objects.create_user(
            username="sessionviewer",
            password="Session-Viewer-Password-2026!",
            is_staff=True,
        )
        view_permission = Permission.objects.get_by_natural_key(
            "view_session", "sessions", "session"
        )
        manager.user_permissions.add(view_permission)
        self.client.force_login(manager)

        response = self.client.get(reverse("admin:sessions_session_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'value="delete_expired_sessions"')

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



class OwnerAccountTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="rootowner",
            email="root@example.com",
            password="Root-Test-Password-2026!",
        )
        self.client.force_login(self.owner)

    def test_owner_can_open_account_settings_and_password_change(self):
        response = self.client.get(reverse("owner_account"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="email"')
        self.assertNotContains(response, 'name="first_name"')
        self.assertNotContains(response, 'name="last_name"')
        self.assertContains(response, reverse("admin:password_change"))
        self.assertContains(response, 'class="button button-primary"')

    def test_owner_can_update_username_and_email_without_changing_other_account_data(self):
        self.owner.first_name = "Existing"
        self.owner.last_name = "Owner Name"
        self.owner.save(update_fields=["first_name", "last_name"])

        response = self.client.post(
            reverse("owner_account"),
            {
                "username": "siteowner",
                "email": "owner@example.com",
                "first_name": "Should Not Be Saved",
                "last_name": "Should Not Be Saved",
                "is_superuser": "",
                "is_staff": "",
            },
        )
        self.assertRedirects(response, reverse("owner_account"))

        self.owner.refresh_from_db()
        self.assertEqual(self.owner.username, "siteowner")
        self.assertEqual(self.owner.email, "owner@example.com")
        self.assertEqual(self.owner.first_name, "Existing")
        self.assertEqual(self.owner.last_name, "Owner Name")
        self.assertTrue(self.owner.is_superuser)
        self.assertTrue(self.owner.is_staff)

    def test_regular_staff_manager_cannot_open_owner_account_settings(self):
        manager = User.objects.create_user(
            username="ordinarymanager",
            password="Manager-Test-Password-2026!",
            is_staff=True,
        )
        self.client.force_login(manager)
        response = self.client.get(reverse("owner_account"))
        self.assertEqual(response.status_code, 403)

    def test_owner_can_use_django_password_change_view(self):
        response = self.client.get(reverse("admin:password_change"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="old_password"')



class AdminPresentationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="adminpresentation",
            email="adminpresentation@example.com",
            password="Admin-Presentation-Password-2026!",
        )
        self.client.force_login(self.owner)

    def test_property_changelist_has_last_edited_column_and_status_widget_class(self):
        Property.objects.create(
            title="فایل جهت بررسی پنل",
            deal_type=Property.DEAL_SALE,
            usage_type=Property.USAGE_RESIDENTIAL,
            property_type=Property.PT_APARTMENT,
            city="تهران",
        )
        response = self.client.get(reverse("admin:listings_property_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "آخرین ویرایش")
        self.assertContains(response, 'property-status-select')
        # The changelist must load the JS that colors its editable status field.
        self.assertContains(response, "listings/js/property_admin.js")

    def test_changelist_filters_are_above_the_table_and_collapsed(self):
        response = self.client.get(reverse("admin:listings_property_changelist"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertLess(content.index('id="changelist-filter"'), content.index('id="changelist"'))
        filter_panel = content.split('id="changelist-filter"', 1)[1].split('</search>', 1)[0]
        self.assertIn("<details data-filter-title=", filter_panel)
        detail_tags = [part.split(">", 1)[0] for part in filter_panel.split("<details")[1:]]
        self.assertTrue(all(" open" not in tag for tag in detail_tags))

    def test_sidebar_section_titles_are_plain_text_not_links(self):
        response = self.client.get(reverse("admin:listings_property_changelist"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('<span class="section">فایل‌های ملکی</span>', content)
        self.assertNotIn('<a href="" class="section">فایل‌های ملکی</a>', content)


class EnhancedPropertySearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Property.objects.create(
            title="آپارتمان مناسب زعفرانیه",
            deal_type=Property.DEAL_SALE,
            usage_type=Property.USAGE_RESIDENTIAL,
            property_type=Property.PT_APARTMENT,
            province="تهران",
            city="کرج",
            neighborhood="زعفرانیه",
            area=120,
            bedrooms=3,
            price=3_500_000_000,
            status=Property.STATUS_ACTIVE,
        )
        Property.objects.create(
            title="واحد اجاره‌ای مرکز شهر",
            deal_type=Property.DEAL_RENT,
            usage_type=Property.USAGE_RESIDENTIAL,
            property_type=Property.PT_APARTMENT,
            province="تهران",
            city="تهران",
            area=85,
            bedrooms=2,
            deposit=400_000_000,
            rent=18_000_000,
            status=Property.STATUS_ACTIVE,
        )

    def test_search_normalizes_arabic_letters_and_punctuation(self):
        response = self.client.get(
            reverse("listings:list"),
            {"q": "كرج، زعفرانيه"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["count"], 1)
        self.assertContains(response, "آپارتمان مناسب زعفرانیه")

    def test_numeric_search_term_can_match_exact_area(self):
        response = self.client.get(
            reverse("listings:list"),
            {"q": "زعفرانیه ۱۲۰"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["count"], 1)

    def test_area_range_filters_are_visible_and_combined(self):
        response = self.client.get(
            reverse("listings:list"),
            {"min_area": "۱۰۰", "max_area": "۱۳۰"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["count"], 1)
        self.assertContains(response, 'name="min_area"')
        self.assertContains(response, 'name="max_area"')

    def test_price_sort_without_deal_type_falls_back_to_newest(self):
        response = self.client.get(
            reverse("listings:list"),
            {"sort": "price_asc"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sort"], "newest")
        self.assertEqual(response.context["count"], 2)


class PropertyDetailNumberTests(TestCase):
    def test_detail_page_formats_sale_and_rental_money_in_persian(self):
        sale = Property.objects.create(
            title="فایل فروش برای جزئیات",
            deal_type=Property.DEAL_SALE,
            usage_type=Property.USAGE_RESIDENTIAL,
            property_type=Property.PT_APARTMENT,
            price=1_234_567_890,
            price_per_meter=12_345_678,
            status=Property.STATUS_ACTIVE,
        )
        rent = Property.objects.create(
            title="فایل اجاره برای جزئیات",
            deal_type=Property.DEAL_RENT,
            usage_type=Property.USAGE_RESIDENTIAL,
            property_type=Property.PT_APARTMENT,
            deposit=987_654_321,
            rent=45_678_900,
            status=Property.STATUS_ACTIVE,
        )

        sale_response = self.client.get(reverse("listings:detail", args=[sale.pk]))
        rent_response = self.client.get(reverse("listings:detail", args=[rent.pk]))

        self.assertEqual(sale_response.status_code, 200)
        self.assertEqual(rent_response.status_code, 200)
        self.assertContains(sale_response, "۱٬۲۳۴٬۵۶۷٬۸۹۰")
        self.assertContains(sale_response, "۱۲٬۳۴۵٬۶۷۸")
        self.assertContains(sale_response, "تومان")
        self.assertContains(rent_response, "۹۸۷٬۶۵۴٬۳۲۱")
        self.assertContains(rent_response, "۴۵٬۶۷۸٬۹۰۰")
        self.assertContains(rent_response, "تومان")
        self.assertContains(sale_response, "js/main.js")
        self.assertContains(rent_response, "js/main.js")



class ContactManagementInterfaceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="contactowner",
            email="contactowner@example.com",
            password="Contact-Owner-Password-2026!",
        )
        self.client.force_login(self.owner)

    def test_contact_admin_renders_local_visual_icon_selector(self):
        response = self.client.get(
            reverse("admin:listings_contactpage_changelist"),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "contact_icon_picker.js")
        self.assertContains(response, "contact-icon-select")
        self.assertContains(response, "data-icon-sprite")
        self.assertContains(response, 'data-icon="headset"')
        self.assertContains(response, "تقویم و زمان مراجعه")

    def test_contact_item_icon_choices_include_varied_contact_categories(self):
        choices = dict(ContactItem.TYPE_CHOICES)
        for value in ("phone", "mobile", "email", "address", "website", "map", "support", "headset", "video"):
            self.assertIn(value, choices)

    def test_social_platform_choices_include_requested_local_messengers(self):
        choices = dict(SocialLink.PLATFORM_CHOICES)
        self.assertEqual(choices["eitaa"], "ایتا")
        self.assertEqual(choices["soroush"], "سروش")
        self.assertEqual(choices["bale"], "بله")
        self.assertEqual(choices["rubika"], "روبیکا")
        self.assertEqual(choices["shad"], "شاد")


class PropertyMediaGalleryTests(TestCase):
    def setUp(self):
        self.property = Property.objects.create(
            title="آپارتمان دارای رسانه",
            deal_type=Property.DEAL_SALE,
            usage_type=Property.USAGE_RESIDENTIAL,
            property_type=Property.PT_APARTMENT,
            status=Property.STATUS_ACTIVE,
        )

    def test_gallery_renders_navigation_accessibility_and_local_video_controls(self):
        PropertyImage.objects.create(
            property=self.property,
            image="properties/images/gallery-test.jpg",
            caption="نمای پذیرایی",
        )
        PropertyVideo.objects.create(
            property=self.property,
            video_file="properties/videos/tour-test.mp4",
            poster="properties/video_posters/tour-poster.jpg",
            title="بازدید ویدئویی",
        )
        response = self.client.get(reverse("listings:detail", args=[self.property.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-property-gallery")
        self.assertContains(response, "data-gallery-prev")
        self.assertContains(response, "data-gallery-next")
        self.assertContains(response, "data-gallery-fullscreen")
        self.assertContains(response, 'role="tablist"')
        self.assertContains(response, 'aria-roledescription="carousel"')
        self.assertContains(response, 'controls playsinline preload="metadata"')
        self.assertContains(response, "بازدید ویدئویی")

    def test_gallery_embeds_recognized_video_provider_and_does_not_trust_similar_hosts(self):
        PropertyVideo.objects.create(
            property=self.property,
            video_url="https://www.youtube.com/watch?v=abc123xyz90",
            title="ویدئوی یوتیوب",
        )
        PropertyVideo.objects.create(
            property=self.property,
            video_url="https://youtube.com.evil.example/watch?v=abc123xyz90",
            title="پیوند خارجی",
        )
        response = self.client.get(reverse("listings:detail", args=[self.property.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'src="https://www.youtube-nocookie.com/embed/abc123xyz90?enablejsapi=1"')
        self.assertContains(response, 'href="https://youtube.com.evil.example/watch?v=abc123xyz90"')
        self.assertContains(response, "بازکردن ویدئو")
        self.assertEqual(response.content.decode().count("<iframe"), 1)
