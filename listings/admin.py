from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.shortcuts import redirect
from django.urls import reverse

from .models import (
    Property, PropertyImage, PropertyVideo,
    UserProfile, SiteSettings, ContactItem, SocialLink, Ticket,
)

# ---------- حذف کامل گروه‌ها ----------
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


# ---------- دسترسی نقش‌محور ----------
class RolePermissionMixin:
    """با ارث‌بری از این کلاس و تعیین allowed_roles، فقط نقش‌های مشخص اجازهٔ دسترسی می‌گیرند."""
    allowed_roles = ()

    def _allowed(self, request):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        try:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            return profile.role in self.allowed_roles
        except Exception:
            return False

    def has_module_permission(self, request):
        return self._allowed(request)

    def has_view_permission(self, request, obj=None):
        return self._allowed(request)

    def has_add_permission(self, request):
        return self._allowed(request)

    def has_change_permission(self, request, obj=None):
        return self._allowed(request)

    def has_delete_permission(self, request, obj=None):
        return self._allowed(request)


# ---------- اینلاین‌های ملک ----------
class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 3
    fields = ('image', 'caption', 'order')


class PropertyVideoInline(admin.TabularInline):
    model = PropertyVideo
    extra = 1
    fields = ('video_file', 'video_url', 'poster', 'title', 'order')


# ---------- پنل فایل‌های ملکی ----------
@admin.register(Property)
class PropertyAdmin(RolePermissionMixin, admin.ModelAdmin):
    allowed_roles = (UserProfile.ROLE_PROPERTY,)
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


# ---------- پنل تنظیمات سایت (تک‌نسخه‌ای) ----------
@admin.register(SiteSettings)
class SiteSettingsAdmin(RolePermissionMixin, admin.ModelAdmin):
    allowed_roles = (UserProfile.ROLE_CONTENT,)

    fieldsets = (
        ('برندینگ', {
            'fields': ('site_name', 'site_description', 'logo'),
            'description': 'اطلاعات پایهٔ برند در سربرگ و فوتر نمایش داده می‌شود.'
        }),
        ('بنر صفحهٔ اصلی', {
            'fields': ('banner_image', 'banner_title', 'banner_subtitle'),
            'description': 'اگر تصویر خالی باشد، پس‌زمینهٔ گرادیانی جایگزین می‌شود.'
        }),
        ('دربارهٔ ما', {
            'fields': ('about_text',),
        }),
    )

    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.load()
        return redirect(reverse('admin:listings_sitesettings_change', args=[obj.pk]))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ---------- اطلاعات تماس ----------
@admin.register(ContactItem)
class ContactItemAdmin(RolePermissionMixin, admin.ModelAdmin):
    allowed_roles = (UserProfile.ROLE_CONTENT,)
    list_display = ('label', 'item_type', 'value', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('item_type', 'is_active')
    search_fields = ('label', 'value')


# ---------- شبکه‌های اجتماعی ----------
@admin.register(SocialLink)
class SocialLinkAdmin(RolePermissionMixin, admin.ModelAdmin):
    allowed_roles = (UserProfile.ROLE_CONTENT,)
    list_display = ('platform', 'url', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('platform', 'is_active')


# ---------- تیکت‌ها ----------
@admin.register(Ticket)
class TicketAdmin(RolePermissionMixin, admin.ModelAdmin):
    allowed_roles = (UserProfile.ROLE_TICKET,)
    list_display = ('id', 'subject', 'name', 'phone', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'phone', 'email', 'subject', 'message')
    readonly_fields = ('name', 'phone', 'email', 'subject', 'message', 'created_at')
    list_editable = ('status',)
    fieldsets = (
        ('اطلاعات تیکت', {
            'fields': ('name', 'phone', 'email', 'subject', 'message', 'created_at')
        }),
        ('مدیریت', {
            'fields': ('status', 'admin_note')
        }),
    )

    def has_add_permission(self, request):
        return False


# ---------- کاربران و نقش‌ها ----------
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    max_num = 1
    fk_name = 'user'
    verbose_name_plural = 'نقش و دسترسی'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'role_display', 'is_active', 'is_staff', 'is_superuser')
    list_filter = ('is_active', 'is_staff', 'is_superuser')

    def role_display(self, obj):
        if obj.is_superuser:
            return 'مدیر ارشد (Superuser)'
        try:
            return obj.profile.get_role_display()
        except Exception:
            return '—'
    role_display.short_description = 'نقش'

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, UserAdmin)


# ---------- برندینگ پنل ----------
admin.site.site_header = 'پنل مدیریت املاک'
admin.site.site_title = 'مدیریت املاک'
admin.site.index_title = 'به پنل مدیریت خوش آمدید'