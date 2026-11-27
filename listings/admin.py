from datetime import timedelta

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group
from django.contrib.sessions.models import Session
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Property, PropertyImage, PropertyVideo,
    UserProfile, SiteSettings, ContactItem, SocialLink, Ticket,
)

# ---------- حذف کامل گروه‌ها ----------
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


class RolePermissionMixin:
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

    def has_module_permission(self, request): return self._allowed(request)
    def has_view_permission(self, request, obj=None): return self._allowed(request)
    def has_add_permission(self, request): return self._allowed(request)
    def has_change_permission(self, request, obj=None): return self._allowed(request)
    def has_delete_permission(self, request, obj=None): return self._allowed(request)


class AdminCSSMixin:
    class Media:
        css = {'all': ('admin/css/custom_admin.css',)}


# ---------- ملک ----------
class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 3
    fields = ('image', 'caption', 'order')


class PropertyVideoInline(admin.TabularInline):
    model = PropertyVideo
    extra = 1
    fields = ('video_file', 'video_url', 'poster', 'title', 'order')


@admin.register(Property)
class PropertyAdmin(RolePermissionMixin, admin.ModelAdmin):
    allowed_roles = (UserProfile.ROLE_PROPERTY,)
    list_display = (
        'title', 'deal_type', 'usage_type', 'property_type', 'city',
        'status', 'is_featured', 'created_at',
    )
    list_filter = ('status', 'deal_type', 'usage_type', 'property_type', 'province', 'city', 'is_featured')
    search_fields = ('title', 'city', 'neighborhood', 'address', 'description')
    list_editable = ('status',)
    date_hierarchy = 'created_at'
    inlines = [PropertyImageInline, PropertyVideoInline]

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'status', 'is_featured')
        }),
        ('دسته‌بندی', {
            'fields': ('deal_type', 'usage_type', 'property_type'),
            'description': 'نوع ملک باید با ترکیب «نوع معامله» و «کاربری» سازگار باشد.'
        }),
        ('موقعیت', {
            'fields': ('province', 'city', 'neighborhood', 'address')
        }),
        ('مشخصات', {
            'fields': ('area', 'bedrooms', 'year_built', 'floor', 'total_floors')
        }),
        ('ویژگی‌ها و امکانات', {
            'fields': ('has_elevator', 'has_storage', 'has_parking', 'has_balcony')
        }),
        ('قیمت — فروش', {
            'fields': ('price', 'price_per_meter'),
            'classes': ('sale-price-group',),
        }),
        ('قیمت — اجاره', {
            'fields': ('deposit', 'rent', 'is_convertible'),
            'classes': ('rent-price-group',),
        }),
        ('تماس و توضیحات', {
            'fields': ('phone', 'description')
        }),
    )

    class Media:
        js = ('listings/js/property_admin.js',)


# ---------- تنظیمات سایت ----------
@admin.register(SiteSettings)
class SiteSettingsAdmin(RolePermissionMixin, admin.ModelAdmin):
    allowed_roles = (UserProfile.ROLE_CONTENT,)
    fieldsets = (
        ('برندینگ', {'fields': ('site_name', 'site_description', 'logo')}),
        ('بنر صفحهٔ اصلی', {'fields': ('banner_image', 'banner_title', 'banner_subtitle')}),
        ('دربارهٔ ما', {'fields': ('about_text',)}),
    )

    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.load()
        return redirect(reverse('admin:listings_sitesettings_change', args=[obj.pk]))

    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False


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
class TicketAdmin(RolePermissionMixin, AdminCSSMixin, admin.ModelAdmin):
    allowed_roles = (UserProfile.ROLE_TICKET,)

    list_display = ('view_button', 'subject', 'name', 'phone', 'status_badge', 'created_at')
    list_display_links = None
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'phone', 'email', 'subject', 'message')
    readonly_fields = ('name', 'phone', 'email', 'subject', 'message', 'created_at')
    date_hierarchy = 'created_at'

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

    @admin.display(description='مشاهده')
    def view_button(self, obj):
        return format_html(
            '<a href="{}" class="btn-view-ticket">مشاهده</a>',
            reverse('admin:listings_ticket_change', args=[obj.pk])
        )

    @admin.display(description='وضعیت')
    def status_badge(self, obj):
        return format_html(
            '<span class="custom-badge status-{}">{}</span>',
            obj.status,
            obj.get_status_display()
        )


# ---------- لاگ‌های ادمین ----------

@admin.register(LogEntry)
class LogEntryAdmin(AdminCSSMixin, admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag_display', 'short_message')
    list_filter = ('action_flag', 'content_type', 'action_time')
    search_fields = ('object_repr', 'change_message')
    date_hierarchy = 'action_time'
    list_per_page = 100
    actions = ['delete_old_logs', 'delete_selected_logs']

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in LogEntry._meta.fields]

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    # --- مهم: هر حذف/افزودن/ویرایشِ خودِ LogEntry لاگ نمی‌شود ---
    def log_deletion(self, request, object, object_repr):
        return

    def log_addition(self, request, object, object_repr):
        return

    def log_change(self, request, object, message):
        return

    # --- اکشن داخلی که لاگ می‌سازد را حذف کن ---
    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    @admin.action(
        description='حذف لاگ‌های قدیمی‌تر از ۳۰ روز',
        permissions=['delete'],
    )
    def delete_old_logs(self, request, queryset):
        cutoff = timezone.now() - timedelta(days=30)
        deleted, _ = LogEntry.objects.filter(action_time__lt=cutoff).delete()
        self.message_user(request, f'{deleted} لاگ قدیمی حذف شد.', level='success')

    @admin.action(
        description='حذف لاگ‌های انتخاب‌شده',
        permissions=['delete'],
    )
    def delete_selected_logs(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} لاگ حذف شد.', level='success')

    @admin.display(description='عملیات')
    def action_flag_display(self, obj):
        mapping = {
            1: ('add', 'افزودن'),
            2: ('change', 'ویرایش'),
            3: ('delete', 'حذف'),
        }
        css, label = mapping.get(obj.action_flag, ('change', '—'))
        return format_html('<span class="custom-badge action-{}">{}</span>', css, label)

    @admin.display(description='توضیح')
    def short_message(self, obj):
        msg = (obj.change_message or '').strip()
        if not msg:
            return '—'
        return msg[:80] + ('…' if len(msg) > 80 else '')


# ---------- جلسات (Sessions) ----------
@admin.action(description='حذف جلسات منقضی‌شده')
def delete_expired_sessions(modeladmin, request, queryset):
    deleted, _ = Session.objects.filter(expire_date__lt=timezone.now()).delete()
    modeladmin.message_user(request, f'{deleted} جلسهٔ منقضی حذف شد.', level='success')


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'expire_date', 'is_expired')
    date_hierarchy = 'expire_date'
    list_per_page = 100
    actions = ['delete_expired_sessions']

    def get_readonly_fields(self, request, obj=None):
        return ('session_key', 'expire_date')

    def get_exclude(self, request, obj=None):
        return ('session_data',)

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    @admin.display(boolean=True, description='منقضی شده')
    def is_expired(self, obj):
        return obj.expire_date < timezone.now()


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

    def has_module_permission(self, request): return request.user.is_superuser
    def has_view_permission(self, request, obj=None): return request.user.is_superuser
    def has_add_permission(self, request): return request.user.is_superuser
    def has_change_permission(self, request, obj=None): return request.user.is_superuser
    def has_delete_permission(self, request, obj=None): return request.user.is_superuser


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, UserAdmin)


# ---------- برندینگ پنل ----------
admin.site.site_header = 'پنل مدیریت املاک'
admin.site.site_title = 'مدیریت املاک'
admin.site.index_title = 'به پنل مدیریت خوش آمدید'
