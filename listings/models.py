from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# ---------- فایل ملکی ----------
class Property(models.Model):
    DEAL_SALE = 'sale'
    DEAL_RENT = 'rent'
    DEAL_MORTGAGE = 'mortgage'
    DEAL_CHOICES = [
        (DEAL_SALE, 'فروش'),
        (DEAL_RENT, 'اجاره'),
        (DEAL_MORTGAGE, 'رهن'),
    ]

    PROPERTY_APARTMENT = 'apartment'
    PROPERTY_HOUSE = 'house'
    PROPERTY_VILLA = 'villa'
    PROPERTY_LAND = 'land'
    PROPERTY_OFFICE = 'office'
    PROPERTY_SHOP = 'shop'
    PROPERTY_CHOICES = [
        (PROPERTY_APARTMENT, 'آپارتمان'),
        (PROPERTY_HOUSE, 'خانه'),
        (PROPERTY_VILLA, 'ویلا'),
        (PROPERTY_LAND, 'زمین'),
        (PROPERTY_OFFICE, 'دفتر کار'),
        (PROPERTY_SHOP, 'مغازه'),
    ]

    title = models.CharField(max_length=200, verbose_name='عنوان')
    deal_type = models.CharField(max_length=20, choices=DEAL_CHOICES, verbose_name='نوع معامله')
    property_type = models.CharField(max_length=20, choices=PROPERTY_CHOICES, verbose_name='نوع ملک')

    province = models.CharField(max_length=100, verbose_name='استان')
    city = models.CharField(max_length=100, verbose_name='شهر')
    neighborhood = models.CharField(max_length=100, blank=True, verbose_name='محله')
    address = models.TextField(blank=True, verbose_name='آدرس')

    area = models.PositiveIntegerField(verbose_name='متراژ (متر مربع)')
    bedrooms = models.PositiveSmallIntegerField(default=0, verbose_name='تعداد خواب')
    bathrooms = models.PositiveSmallIntegerField(default=0, verbose_name='تعداد سرویس')
    year_built = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='سال ساخت')
    floor = models.SmallIntegerField(null=True, blank=True, verbose_name='طبقه')
    total_floors = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='تعداد کل طبقات')

    price = models.BigIntegerField(null=True, blank=True, verbose_name='قیمت کل (تومان)')
    deposit = models.BigIntegerField(null=True, blank=True, verbose_name='ودیعه (تومان)')
    rent = models.BigIntegerField(null=True, blank=True, verbose_name='اجاره ماهانه (تومان)')

    phone = models.CharField(max_length=20, blank=True, verbose_name='شماره تماس')

    description = models.TextField(blank=True, verbose_name='توضیحات')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_featured = models.BooleanField(default=False, verbose_name='ویژه')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین ویرایش')

    class Meta:
        verbose_name = 'فایل ملکی'
        verbose_name_plural = 'فایل‌های ملکی'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.city} ({self.get_deal_type_display()})"

    @property
    def main_image(self):
        first = self.images.first()
        return first.image if first else None


class PropertyImage(models.Model):
    property = models.ForeignKey(
        Property, related_name='images', on_delete=models.CASCADE, verbose_name='فایل ملکی'
    )
    image = models.ImageField(upload_to='properties/images/', verbose_name='تصویر')
    caption = models.CharField(max_length=200, blank=True, verbose_name='عنوان تصویر')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='ترتیب')

    class Meta:
        verbose_name = 'تصویر'
        verbose_name_plural = 'تصاویر'
        ordering = ['order', 'id']

    def __str__(self):
        return f"تصویر {self.id} برای {self.property.title}"


class PropertyVideo(models.Model):
    property = models.ForeignKey(
        Property, related_name='videos', on_delete=models.CASCADE, verbose_name='فایل ملکی'
    )
    video_file = models.FileField(
        upload_to='properties/videos/', blank=True, null=True, verbose_name='فایل ویدیو'
    )
    video_url = models.URLField(blank=True, verbose_name='لینک ویدیو (اختیاری)')
    poster = models.ImageField(
        upload_to='properties/video_posters/', blank=True, null=True,
        verbose_name='تصویر بندانگشتی', help_text='اگر خالی باشد، آیکون ویدیو نمایش داده می‌شود.'
    )
    title = models.CharField(max_length=200, blank=True, verbose_name='عنوان ویدیو')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='ترتیب')

    class Meta:
        verbose_name = 'ویدیو'
        verbose_name_plural = 'ویدیوها'
        ordering = ['order', 'id']

    def __str__(self):
        return self.title or f"ویدیو {self.id}"


# ---------- نقش کاربر ادمین ----------
class UserProfile(models.Model):
    ROLE_SUPER = 'super'
    ROLE_PROPERTY = 'property'
    ROLE_TICKET = 'ticket'
    ROLE_CONTENT = 'content'
    ROLE_CHOICES = [
        (ROLE_SUPER, 'مدیر ارشد — دسترسی کامل'),
        (ROLE_PROPERTY, 'مدیر املاک — فقط فایل‌های ملکی'),
        (ROLE_TICKET, 'مدیر تیکت‌ها'),
        (ROLE_CONTENT, 'مدیر محتوا — تنظیمات، تماس، شبکه‌ها'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_PROPERTY, verbose_name='نقش')

    class Meta:
        verbose_name = 'نقش کاربر'
        verbose_name_plural = 'نقش کاربران'

    def __str__(self):
        return f"{self.user.username} — {self.get_role_display()}"


@receiver(post_save, sender=User)
def _ensure_profile(sender, instance, **kwargs):
    UserProfile.objects.get_or_create(user=instance)


# ---------- تنظیمات سایت (تک‌نسخه‌ای) ----------
class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default='املاک نمونه', verbose_name='نام بنگاه')
    site_description = models.CharField(
        max_length=200, blank=True,
        verbose_name='توضیح کوتاه', help_text='زیر نام بنگاه در سربرگ نمایش داده می‌شود.'
    )
    logo = models.ImageField(
        upload_to='site/', blank=True, null=True,
        verbose_name='لوگو', help_text='اگر خالی باشد، حرف اول نام بنگاه نمایش داده می‌شود.'
    )

    banner_image = models.ImageField(
        upload_to='site/banners/', blank=True, null=True,
        verbose_name='تصویر بنر',
        help_text='اگر خالی باشد، پس‌زمینهٔ گرادیانی زیبا نمایش داده می‌شود.'
    )
    banner_title = models.CharField(max_length=200, blank=True, verbose_name='عنوان بنر')
    banner_subtitle = models.CharField(max_length=300, blank=True, verbose_name='زیرعنوان بنر')

    about_text = models.TextField(blank=True, verbose_name='دربارهٔ ما')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'تنظیمات سایت'
        verbose_name_plural = 'تنظیمات سایت'

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def logo_letter(self):
        return (self.site_name or 'ا')[:1]


# ---------- اطلاعات تماس ----------
class ContactItem(models.Model):
    TYPE_PHONE = 'phone'
    TYPE_MOBILE = 'mobile'
    TYPE_EMAIL = 'email'
    TYPE_ADDRESS = 'address'
    TYPE_FAX = 'fax'
    TYPE_HOURS = 'hours'
    TYPE_CUSTOM = 'custom'
    TYPE_CHOICES = [
        (TYPE_PHONE, 'تلفن ثابت'),
        (TYPE_MOBILE, 'همراه'),
        (TYPE_EMAIL, 'ایمیل'),
        (TYPE_ADDRESS, 'آدرس'),
        (TYPE_FAX, 'فکس'),
        (TYPE_HOURS, 'ساعات کاری'),
        (TYPE_CUSTOM, 'سایر'),
    ]
    ICONS = {
        TYPE_PHONE: '📞', TYPE_MOBILE: '📱', TYPE_EMAIL: '✉️',
        TYPE_ADDRESS: '📍', TYPE_FAX: '📠', TYPE_HOURS: '🕒', TYPE_CUSTOM: '•',
    }

    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_CUSTOM, verbose_name='نوع')
    label = models.CharField(max_length=100, verbose_name='عنوان نمایشی')
    value = models.CharField(max_length=300, verbose_name='مقدار')
    link = models.CharField(
        max_length=300, blank=True, verbose_name='لینک',
        help_text='اختیاری، مثل tel:02112345678 یا mailto:info@example.com'
    )
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب')
    is_active = models.BooleanField(default=True, verbose_name='فعال')

    class Meta:
        verbose_name = 'اطلاعات تماس'
        verbose_name_plural = 'اطلاعات تماس'
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.label}: {self.value}"

    @property
    def icon(self):
        return self.ICONS.get(self.item_type, '•')


# ---------- شبکه‌های اجتماعی ----------
class SocialLink(models.Model):
    PLATFORM_CHOICES = [
        ('instagram', 'اینستاگرام'),
        ('telegram', 'تلگرام'),
        ('whatsapp', 'واتساپ'),
        ('x', 'X (توییتر)'),
        ('linkedin', 'لینکدین'),
        ('youtube', 'یوتیوب'),
        ('aparat', 'آپارات'),
        ('facebook', 'فیسبوک'),
    ]
    ICONS = {
        'instagram': '📷', 'telegram': '✈️', 'whatsapp': '💬',
        'x': '𝕏', 'linkedin': '💼', 'youtube': '▶️',
        'aparat': '🎬', 'facebook': '📘',
    }
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, verbose_name='پلتفرم')
    url = models.URLField(verbose_name='لینک')
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب')
    is_active = models.BooleanField(default=True, verbose_name='فعال')

    class Meta:
        verbose_name = 'شبکهٔ اجتماعی'
        verbose_name_plural = 'شبکه‌های اجتماعی'
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.get_platform_display()} — {self.url}"

    @property
    def icon(self):
        return self.ICONS.get(self.platform, '🔗')


# ---------- تیکت ----------
class Ticket(models.Model):
    STATUS_NEW = 'new'
    STATUS_READ = 'read'
    STATUS_REPLIED = 'replied'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_NEW, 'جدید'),
        (STATUS_READ, 'خوانده شده'),
        (STATUS_REPLIED, 'پاسخ داده شده'),
        (STATUS_CLOSED, 'بسته شده'),
    ]
    name = models.CharField(max_length=100, verbose_name='نام فرستنده')
    phone = models.CharField(max_length=30, verbose_name='تلفن')
    email = models.EmailField(blank=True, verbose_name='ایمیل')
    subject = models.CharField(max_length=200, verbose_name='موضوع')
    message = models.TextField(verbose_name='پیام')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW, verbose_name='وضعیت')
    admin_note = models.TextField(blank=True, verbose_name='یادداشت / پاسخ ادمین')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')

    class Meta:
        verbose_name = 'تیکت'
        verbose_name_plural = 'تیکت‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f"تیکت #{self.pk} — {self.subject}"