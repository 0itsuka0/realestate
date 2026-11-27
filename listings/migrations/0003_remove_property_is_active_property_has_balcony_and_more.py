from django.db import migrations, models


def preserve_is_active(apps, schema_editor):
    Property = apps.get_model('listings', 'Property')
    Property.objects.filter(is_active=False).update(status='suspended')


def restore_is_active(apps, schema_editor):
    Property = apps.get_model('listings', 'Property')
    Property.objects.filter(status='suspended').update(is_active=False)


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0002_contactitem_sitesettings_sociallink_ticket_and_more'),
    ]

    operations = [
        # --- ابتدا فیلدهای جدید ---
        migrations.AddField(
            model_name='property',
            name='has_balcony',
            field=models.BooleanField(default=False, verbose_name='بالکن'),
        ),
        migrations.AddField(
            model_name='property',
            name='has_elevator',
            field=models.BooleanField(default=False, verbose_name='آسانسور'),
        ),
        migrations.AddField(
            model_name='property',
            name='has_parking',
            field=models.BooleanField(default=False, verbose_name='پارکینگ'),
        ),
        migrations.AddField(
            model_name='property',
            name='has_storage',
            field=models.BooleanField(default=False, verbose_name='انباری'),
        ),
        migrations.AddField(
            model_name='property',
            name='is_convertible',
            field=models.BooleanField(default=True, verbose_name='ودیعه و اجاره قابل تبدیل'),
        ),
        migrations.AddField(
            model_name='property',
            name='price_per_meter',
            field=models.BigIntegerField(blank=True, null=True, verbose_name='قیمت هر متر (تومان)'),
        ),
        migrations.AddField(
            model_name='property',
            name='rent_type',
            field=models.CharField(blank=True, choices=[('deposit_only', 'ودیعه'), ('rent_only', 'اجاره ماهانه'), ('both', 'ودیعه و اجاره')], default='', help_text='فقط برای اجاره. اگر «ودیعه و اجاره» را انتخاب کردید، وضعیت قابل تبدیل را هم مشخص کنید.', max_length=20, verbose_name='نوع اجاره'),
        ),
        migrations.AddField(
            model_name='property',
            name='status',
            field=models.CharField(choices=[('active', 'فعال'), ('suspended', 'معلق'), ('sold', 'معامله شده'), ('cancelled', 'لغو شده')], default='active', max_length=20, verbose_name='وضعیت فایل'),
        ),
        migrations.AddField(
            model_name='property',
            name='usage_type',
            field=models.CharField(choices=[('residential', 'مسکونی'), ('commercial', 'اداری تجاری')], default='residential', max_length=20, verbose_name='کاربری'),
        ),
        # --- کپی داده از is_active به status ---
        migrations.RunPython(preserve_is_active, restore_is_active),
        # --- حالا فیلد قدیمی حذف شود ---
        migrations.RemoveField(
            model_name='property',
            name='is_active',
        ),
        # --- AlterFieldهای Django ---
        migrations.AlterField(
            model_name='contactitem',
            name='link',
            field=models.CharField(blank=True, max_length=300, verbose_name='لینک'),
        ),
        migrations.AlterField(
            model_name='property',
            name='area',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='متراژ (متر مربع)'),
        ),
        migrations.AlterField(
            model_name='property',
            name='bathrooms',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='تعداد سرویس'),
        ),
        migrations.AlterField(
            model_name='property',
            name='bedrooms',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='تعداد اتاق'),
        ),
        migrations.AlterField(
            model_name='property',
            name='city',
            field=models.CharField(blank=True, max_length=100, verbose_name='شهر'),
        ),
        migrations.AlterField(
            model_name='property',
            name='deal_type',
            field=models.CharField(choices=[('sale', 'فروش'), ('rent', 'اجاره')], default='sale', max_length=20, verbose_name='نوع معامله'),
        ),
        migrations.AlterField(
            model_name='property',
            name='property_type',
            field=models.CharField(choices=[('apartment', 'آپارتمان'), ('house_villa', 'خانه و ویلا'), ('land_old', 'زمین و ملک کلنگی'), ('office', 'دفترکار، اتاق اداری، مطب'), ('shop', 'مغازه و غرفه'), ('industrial', 'صنعتی، کشاورزی، تجاری')], max_length=20, verbose_name='نوع ملک'),
        ),
        migrations.AlterField(
            model_name='property',
            name='province',
            field=models.CharField(blank=True, max_length=100, verbose_name='استان'),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='banner_image',
            field=models.ImageField(blank=True, null=True, upload_to='site/banners/', verbose_name='تصویر بنر'),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to='site/', verbose_name='لوگو'),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='site_description',
            field=models.CharField(blank=True, max_length=200, verbose_name='توضیح کوتاه'),
        ),
    ]