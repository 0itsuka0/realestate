from django.db import migrations


def attach_legacy_contact_items(apps, schema_editor):
    ContactPage = apps.get_model("listings", "ContactPage")
    ContactItem = apps.get_model("listings", "ContactItem")
    SocialLink = apps.get_model("listings", "SocialLink")

    page, _ = ContactPage.objects.get_or_create(pk=1)
    ContactItem.objects.filter(contact_page__isnull=True).update(contact_page_id=page.pk)
    SocialLink.objects.filter(contact_page__isnull=True).update(contact_page_id=page.pk)


class Migration(migrations.Migration):
    dependencies = [
        ("listings", "0006_contactpage_contactitem_contact_page_and_more"),
    ]

    operations = [
        migrations.RunPython(attach_legacy_contact_items, migrations.RunPython.noop),
    ]
