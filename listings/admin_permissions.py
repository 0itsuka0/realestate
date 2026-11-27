"""Section-level checkbox mapping to Django's built-in model permissions."""

from django.contrib.auth.models import Permission


ALL_MODEL_ACTIONS = ("add", "change", "delete", "view")

SECTION_PERMISSION_RULES = {
    "can_manage_properties": {
        "label": "فایل‌های ملکی",
        "models": (
            ("listings", "property", ALL_MODEL_ACTIONS),
            ("listings", "propertyimage", ALL_MODEL_ACTIONS),
            ("listings", "propertyvideo", ALL_MODEL_ACTIONS),
        ),
    },
    "can_manage_contact": {
        "label": "اطلاعات تماس و شبکه‌های اجتماعی",
        "models": (
            ("listings", "contactpage", ALL_MODEL_ACTIONS),
            ("listings", "contactitem", ALL_MODEL_ACTIONS),
            ("listings", "sociallink", ALL_MODEL_ACTIONS),
        ),
    },
    "can_manage_tickets": {
        "label": "تیکت‌ها",
        "models": (("listings", "ticket", ALL_MODEL_ACTIONS),),
    },
    "can_manage_site_settings": {
        "label": "تنظیمات سایت",
        "models": (("listings", "sitesettings", ALL_MODEL_ACTIONS),),
    },
    "can_view_logs": {
        "label": "لاگ‌های سیستم",
        "models": (("admin", "logentry", ("view", "delete")),),
    },
    "can_manage_sessions": {
        "label": "مدیریت نشست‌ها",
        "models": (("sessions", "session", ("view", "delete")),),
    },
}

SECTION_PERMISSION_FIELDS = tuple(SECTION_PERMISSION_RULES)


def section_permission_strings(field_name):
    """Return Django permission strings represented by one section checkbox."""
    rule = SECTION_PERMISSION_RULES[field_name]
    return tuple(
        f"{app_label}.{action}_{model}"
        for app_label, model, actions in rule["models"]
        for action in actions
    )


def permissions_for_sections(selected_fields):
    """Resolve selected section checkboxes to Django Permission objects."""
    permissions = {}
    for field_name, rule in SECTION_PERMISSION_RULES.items():
        if not selected_fields.get(field_name, False):
            continue
        for app_label, model, actions in rule["models"]:
            for action in actions:
                codename = f"{action}_{model}"
                permission = Permission.objects.get_by_natural_key(
                    codename, app_label, model
                )
                permissions[permission.pk] = permission
    return list(permissions.values())
