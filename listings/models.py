from django.db import models


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
    title = models.CharField(max_length=200, blank=True, verbose_name='عنوان ویدیو')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='ترتیب')

    class Meta:
        verbose_name = 'ویدیو'
        verbose_name_plural = 'ویدیوها'
        ordering = ['order', 'id']

    def __str__(self):
        return self.title or f"ویدیو {self.id}"