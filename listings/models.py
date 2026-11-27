from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# ---------- فایل ملکی ----------
class Property(models.Model):
    # نوع معامله
    DEAL_SALE = 'sale'
    DEAL_RENT = 'rent'
    DEAL_CHOICES = [
        (DEAL_SALE, 'فروش'),
        (DEAL_RENT, 'اجاره'),
    ]

    # کاربری
    USAGE_RESIDENTIAL = 'residential'
    USAGE_COMMERCIAL = 'commercial'
    USAGE_CHOICES = [
        (USAGE_RESIDENTIAL, 'مسکونی'),
        (USAGE_COMMERCIAL, 'اداری تجاری'),
    ]

    # نوع ملک
    PT_APARTMENT = 'apartment'
    PT_HOUSE_VILLA = 'house_villa'
    PT_LAND_OLD = 'land_old'
    PT_OFFICE = 'office'
    PT_SHOP = 'shop'
    PT_INDUSTRIAL = 'industrial'
    PT_CHOICES = [
        (PT_APARTMENT, 'آپارتمان'),
        (PT_HOUSE_VILLA, 'خانه و ویلا'),
        (PT_LAND_OLD, 'زمین و ملک کلنگی'),
        (PT_OFFICE, 'دفترکار، اتاق اداری، مطب'),
        (PT_SHOP, 'مغازه و غرفه'),
        (PT_INDUSTRIAL, 'صنعتی، کشاورزی، تجاری'),
    ]

    # ماتریس مجاز: هر ترکیب deal_type + usage_type چه نوع ملکی می‌پذیرد
    PT_MATRIX = {
        (DEAL_RENT, USAGE_RESIDENTIAL): [PT_APARTMENT, PT_HOUSE_VILLA],
        (DEAL_SALE, USAGE_RESIDENTIAL): [PT_APARTMENT, PT_HOUSE_VILLA, PT_LAND_OLD],
        (DEAL_RENT, USAGE_COMMERCIAL): [PT_OFFICE, PT_SHOP, PT_INDUSTRIAL],
        (DEAL_SALE, USAGE_COMMERCIAL): [PT_OFFICE, PT_SHOP, PT_INDUSTRIAL],
    }

    # وضعیت فایل
    STATUS_ACTIVE = 'active'
    STATUS_SUSPENDED = 'suspended'
    STATUS_SOLD = 'sold'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'فعال'),
        (STATUS_SUSPENDED, 'معلق'),
        (STATUS_SOLD, 'معامله شده'),
        (STATUS_CANCELLED, 'لغو شده'),
    ]

    # --- فیلدهای ضروری ---
    title = models.CharField(max_length=200, verbose_name='عنوان')
    deal_type = models.CharField(max_length=20, choices=DEAL_CHOICES, default=DEAL_SALE, verbose_name='نوع معامله')
    usage_type = models.CharField(max_length=20, choices=USAGE_CHOICES, default=USAGE_RESIDENTIAL, verbose_name='کاربری')
    property_type = models.CharField(max_length=20, choices=PT_CHOICES, verbose_name='نوع ملک')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE, verbose_name='وضعیت فایل')

    # --- موقعیت (اختیاری) ---
    province = models.CharField(max_length=100, blank=True, verbose_name='استان')
    city = models.CharField(max_length=100, blank=True, verbose_name='شهر')
    neighborhood = models.CharField(max_length=100, blank=True, verbose_name='محله')
    address = models.TextField(blank=True, verbose_name='آدرس')

    # --- مشخصات (اختیاری) ---
    area = models.PositiveIntegerField(null=True, blank=True, verbose_name='متراژ (متر مربع)')
    bedrooms = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='تعداد اتاق')
    year_built = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='سال ساخت')
    floor = models.SmallIntegerField(null=True, blank=True, verbose_name='طبقه')
    total_floors = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='تعداد کل طبقات')

    # --- ویژگی‌ها و امکانات ---
    has_elevator = models.BooleanField(default=False, verbose_name='آسانسور')
    has_storage = models.BooleanField(default=False, verbose_name='انباری')
    has_parking = models.BooleanField(default=False, verbose_name='پارکینگ')
    has_balcony = models.BooleanField(default=False, verbose_name='بالکن')

    # --- قیمت: فروش ---
    price = models.BigIntegerField(null=True, blank=True, verbose_name='قیمت کل (تومان)')
    price_per_meter = models.BigIntegerField(null=True, blank=True, verbose_name='قیمت هر متر (تومان)')

    # --- قیمت: اجاره ---
    deposit = models.BigIntegerField(null=True, blank=True, verbose_name='ودیعه (تومان)')
    rent = models.BigIntegerField(null=True, blank=True, verbose_name='اجاره ماهانه (تومان)')
    is_convertible = models.BooleanField(default=True, verbose_name='ودیعه و اجاره قابل تبدیل')

    # --- تماس و توضیحات ---
    phone = models.CharField(max_length=20, blank=True, verbose_name='شماره تماس')
    description = models.TextField(blank=True, verbose_name='توضیحات')

    # --- ویژه ---
    is_featured = models.BooleanField(default=False, verbose_name='ویژه')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین ویرایش')

    class Meta:
        verbose_name = 'فایل ملکی'
        verbose_name_plural = 'فایل‌های ملکی'
        ordering = ['-created_at']

    def clean(self):
        from django.core.exceptions import ValidationError
        errors = {}
        if self.deal_type and self.usage_type and self.property_type:
            allowed = self.PT_MATRIX.get((self.deal_type, self.usage_type), [])
            if self.property_type not in allowed:
                errors['property_type'] = 'این نوع ملک با کاربری و نوع معاملهٔ انتخاب‌شده سازگار نیست.'
        if errors:
            raise ValidationError(errors)

    @property
    def main_image(self):
        # Use the prefetch cache when available to avoid one query per property card.
        prefetched = getattr(self, "_prefetched_objects_cache", {}).get("images")
        if prefetched is not None:
            return prefetched[0].image if prefetched else None
        first = self.images.first()
        return first.image if first else None

    @property
    def is_active(self):
        return self.status == self.STATUS_ACTIVE

    def __str__(self):
        return f"{self.title} — {self.city} ({self.get_deal_type_display()})"


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


# ---------- تنظیمات سایت ----------
class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default='املاک نمونه', verbose_name='نام بنگاه')
    site_description = models.CharField(max_length=200, blank=True, verbose_name='توضیح کوتاه')
    logo = models.ImageField(upload_to='site/', blank=True, null=True, verbose_name='لوگو')
    banner_image = models.ImageField(
        upload_to='site/banners/', blank=True, null=True, verbose_name='تصویر بنر'
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
class ContactPage(models.Model):
    """نگه‌دارندهٔ صفحهٔ اطلاعات تماس (تک‌نسخه‌ای) — فقط برای نمایش ContactItem و SocialLink در یک صفحه."""
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین ویرایش')

    class Meta:
        verbose_name = 'اطلاعات تماس'
        verbose_name_plural = 'اطلاعات تماس'

    def __str__(self):
        return 'اطلاعات تماس'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

class ContactItem(models.Model):
    contact_page = models.ForeignKey(
        ContactPage, on_delete=models.CASCADE, null=True, blank=True,
        related_name='contact_items', verbose_name='صفحهٔ تماس'
    )
    TYPE_PHONE = 'phone'
    TYPE_MOBILE = 'mobile'
    TYPE_EMAIL = 'email'
    TYPE_ADDRESS = 'address'
    TYPE_FAX = 'fax'
    TYPE_HOURS = 'hours'
    TYPE_CUSTOM = 'custom'
    TYPE_CHOICES = [
        (TYPE_PHONE, 'تلفن ثابت'), (TYPE_MOBILE, 'همراه'),
        (TYPE_EMAIL, 'ایمیل'), (TYPE_ADDRESS, 'آدرس'),
        (TYPE_FAX, 'فکس'), (TYPE_HOURS, 'ساعات کاری'),
        (TYPE_CUSTOM, 'سایر'),
    ]
    ICONS = {
        TYPE_PHONE: '📞', TYPE_MOBILE: '📱', TYPE_EMAIL: '✉️',
        TYPE_ADDRESS: '📍', TYPE_FAX: '📠', TYPE_HOURS: '🕒', TYPE_CUSTOM: '•',
    }
    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_CUSTOM, verbose_name='نوع')
    label = models.CharField(max_length=100, verbose_name='عنوان نمایشی')
    value = models.CharField(max_length=300, verbose_name='مقدار')
    link = models.CharField(max_length=300, blank=True, verbose_name='لینک')
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
    contact_page = models.ForeignKey(
        ContactPage, on_delete=models.CASCADE, null=True, blank=True,
        related_name='social_links', verbose_name='صفحهٔ تماس'
    )
    PLATFORM_CHOICES = [
        ('instagram', 'اینستاگرام'), ('telegram', 'تلگرام'),
        ('whatsapp', 'واتساپ'), ('x', 'X (توییتر)'),
        ('linkedin', 'لینکدین'), ('youtube', 'یوتیوب'),
        ('aparat', 'آپارات'), ('facebook', 'فیسبوک'),
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
        (STATUS_NEW, 'جدید'), (STATUS_READ, 'خوانده شده'),
        (STATUS_REPLIED, 'پاسخ داده شده'), (STATUS_CLOSED, 'بسته شده'),
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
