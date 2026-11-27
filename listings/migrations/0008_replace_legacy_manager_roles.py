from django.db import migrations


# Keep this mapping frozen in the migration so later UI changes do not alter
# how existing role-based accounts are converted.
ALL_ACTIONS = ("add", "change", "delete", "view")

SECTION_MODELS = {
    "properties": (
        ("listings", "property", ALL_ACTIONS),
        ("listings", "propertyimage", ALL_ACTIONS),
        ("listings", "propertyvideo", ALL_ACTIONS),
    ),
    "contact": (
        ("listings", "contactpage", ALL_ACTIONS),
        ("listings", "contactitem", ALL_ACTIONS),
        ("listings", "sociallink", ALL_ACTIONS),
    ),
    "tickets": (
        ("listings", "ticket", ALL_ACTIONS),
    ),
    "site_settings": (
        ("listings", "sitesettings", ALL_ACTIONS),
    ),
    "logs": (
        ("admin", "logentry", ("view", "delete")),
    ),
    "sessions": (
        ("sessions", "session", ("view", "delete")),
    ),
}

ROLE_TO_SECTIONS = {
    "super": tuple(SECTION_MODELS),
    "property": ("properties",),
    "ticket": ("tickets",),
    "content": ("contact", "site_settings"),
}


def migrate_legacy_manager_roles(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("listings", "UserProfile")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")

    alias = schema_editor.connection.alias
    user_permission_through = User.user_permissions.through
    user_group_through = User.groups.through

    for profile in UserProfile.objects.using(alias).all().iterator():
        user = User.objects.using(alias).get(pk=profile.user_id)

        # Public/non-staff accounts and the root superuser do not need manager
        # section permissions.
        if not user.is_staff or user.is_superuser:
            continue

        # This redesigned manager screen has one source of truth: the section
        # checkboxes. Remove old direct/group grants before applying the
        # equivalent of the legacy role.
        user_permission_through.objects.using(alias).filter(user_id=user.pk).delete()
        user_group_through.objects.using(alias).filter(user_id=user.pk).delete()

        selected_sections = ROLE_TO_SECTIONS.get(profile.role, ())
        permission_ids = []

        for section in selected_sections:
            for app_label, model, actions in SECTION_MODELS[section]:
                content_type, _ = ContentType.objects.using(alias).get_or_create(
                    app_label=app_label,
                    model=model,
                )
                for action in actions:
                    codename = f"{action}_{model}"
                    permission, _ = Permission.objects.using(alias).get_or_create(
                        content_type_id=content_type.pk,
                        codename=codename,
                        defaults={
                            "name": f"Can {action} {model.replace('_', ' ')}",
                        },
                    )
                    permission_ids.append(permission.pk)

        user_permission_through.objects.using(alias).bulk_create(
            [
                user_permission_through(
                    user_id=user.pk,
                    permission_id=permission_id,
                )
                for permission_id in permission_ids
            ],
            ignore_conflicts=True,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("listings", "0007_attach_legacy_contact_data"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("admin", "0003_logentry_add_action_flag_choices"),
        ("sessions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            migrate_legacy_manager_roles,
            migrations.RunPython.noop,
        ),
        migrations.DeleteModel(
            name="UserProfile",
        ),
    ]
