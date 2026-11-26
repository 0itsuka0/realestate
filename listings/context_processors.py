from .models import SiteSettings, ContactItem, SocialLink


def site_context(request):
    return {
        'site_settings': SiteSettings.load(),
        'contact_items': ContactItem.objects.filter(is_active=True),
        'social_links': SocialLink.objects.filter(is_active=True),
    }