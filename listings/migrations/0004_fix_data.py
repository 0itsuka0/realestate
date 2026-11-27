from django.db import migrations


def fix_data(apps, schema_editor):
    Property = apps.get_model('listings', 'Property')

    # ۱) رهن → اجاره با نوع "ودیعه"
    Property.objects.filter(deal_type='mortgage').update(
        deal_type='rent',
        rent_type='deposit_only',
    )

    # ۲) برای اجاره‌های موجود، نوع اجاره را استنتاج کن
    for p in Property.objects.filter(deal_type='rent', rent_type=''):
        if p.deposit and p.rent:
            p.rent_type = 'both'
        elif p.deposit:
            p.rent_type = 'deposit_only'
        elif p.rent:
            p.rent_type = 'rent_only'
        p.save(update_fields=['rent_type'])

    # ۳) نگاشت property_type قدیمی به جدید
    Property.objects.filter(property_type='house').update(property_type='house_villa')
    Property.objects.filter(property_type='villa').update(property_type='house_villa')
    Property.objects.filter(property_type='land').update(property_type='land_old')

    # ۴) تعیین usage_type بر اساس property_type
    Property.objects.filter(
        property_type__in=['office', 'shop', 'industrial']
    ).update(usage_type='commercial')
    Property.objects.filter(
        property_type__in=['apartment', 'house_villa', 'land_old']
    ).update(usage_type='residential')


def reverse_fix(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0003_remove_property_is_active_property_has_balcony_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_data, reverse_fix),
    ]