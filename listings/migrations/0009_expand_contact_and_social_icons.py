from django.db import migrations, models


CONTACT_ITEM_CHOICES = [
    ("phone", "تلفن ثابت"),
    ("mobile", "تلفن همراه"),
    ("email", "ایمیل"),
    ("address", "آدرس"),
    ("fax", "فکس"),
    ("hours", "ساعات کاری"),
    ("website", "وب‌سایت"),
    ("map", "نقشه و مسیریابی"),
    ("building", "ساختمان و دفتر"),
    ("support", "پشتیبانی"),
    ("message", "پیام"),
    ("whatsapp", "واتساپ"),
    ("telegram", "تلگرام"),
    ("instagram", "اینستاگرام"),
    ("calendar", "تقویم و زمان مراجعه"),
    ("user", "شخص پاسخ‌گو"),
    ("info", "اطلاعات"),
    ("briefcase", "امور اداری"),
    ("store", "شعبه و فروشگاه"),
    ("link", "پیوند"),
    ("clock", "زمان"),
    ("mail", "صندوق پستی"),
    ("phone-alt", "تماس فوری"),
    ("location", "موقعیت مکانی"),
    ("headset", "مرکز تماس"),
    ("video", "تماس تصویری"),
    ("globe", "آدرس اینترنتی"),
    ("custom", "سایر"),
]

SOCIAL_PLATFORM_CHOICES = [
    ("instagram", "اینستاگرام"),
    ("telegram", "تلگرام"),
    ("whatsapp", "واتساپ"),
    ("x", "X (توییتر)"),
    ("linkedin", "لینکدین"),
    ("youtube", "یوتیوب"),
    ("aparat", "آپارات"),
    ("facebook", "فیسبوک"),
    ("eitaa", "ایتا"),
    ("soroush", "سروش"),
    ("bale", "بله"),
    ("rubika", "روبیکا"),
    ("shad", "شاد"),
]


class Migration(migrations.Migration):
    dependencies = [
        ("listings", "0008_replace_legacy_manager_roles"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contactitem",
            name="item_type",
            field=models.CharField(
                choices=CONTACT_ITEM_CHOICES,
                default="custom",
                max_length=20,
                verbose_name="آیکن",
            ),
        ),
        migrations.AlterField(
            model_name="sociallink",
            name="platform",
            field=models.CharField(
                choices=SOCIAL_PLATFORM_CHOICES,
                max_length=20,
                verbose_name="پلتفرم",
            ),
        ),
    ]
