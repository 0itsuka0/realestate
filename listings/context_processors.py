from .models import ContactPage, SiteSettings


def site_context(request):
    contact_page = ContactPage.load()
    return {
        "site_settings": SiteSettings.load(),
        "contact_page": contact_page,
        "contact_items": contact_page.contact_items.filter(is_active=True),
        "social_links": contact_page.social_links.filter(is_active=True),
    }
