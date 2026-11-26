from django.contrib import admin
from .models import Property, PropertyImage, PropertyVideo


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 3
    fields = ('image', 'caption', 'order')


class PropertyVideoInline(admin.TabularInline):
    model = PropertyVideo
    extra = 1
    fields = ('video_file', 'video_url', 'title', 'order')


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'deal_type', 'property_type', 'city', 'area',
        'price', 'deposit', 'rent', 'is_active', 'created_at',
    )
    list_filter = ('deal_type', 'property_type', 'is_active', 'province', 'city')
    search_fields = ('title', 'city', 'neighborhood', 'address', 'description')
    list_editable = ('is_active',)
    date_hierarchy = 'created_at'
    inlines = [PropertyImageInline, PropertyVideoInline]
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'deal_type', 'property_type', 'is_active', 'is_featured')
        }),
        ('موقعیت', {
            'fields': ('province', 'city', 'neighborhood', 'address')
        }),
        ('مشخصات', {
            'fields': ('area', 'bedrooms', 'bathrooms', 'year_built', 'floor', 'total_floors')
        }),
        ('قیمت', {
            'fields': ('price', 'deposit', 'rent')
        }),
        ('تماس و توضیحات', {
            'fields': ('phone', 'description')
        }),
    )


admin.site.site_header = 'پنل مدیریت املاک'
admin.site.site_title = 'مدیریت املاک'
admin.site.index_title = 'به پنل مدیریت خوش آمدید'