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

from .admin_permissions import (
    SECTION_PERMISSION_FIELDS,
    permissions_for_sections,
)
from .forms import ContactItemAdminForm, ManagerChangeForm, ManagerCreationForm
from .models import (
    Property, PropertyImage, PropertyVideo,
    SiteSettings, ContactItem, SocialLink, Ticket, ContactPage,
)

# ---------- حذف کامل گروه‌ها ----------
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


class AdminCSSMixin:
    class Media:
        css = {'all': ('admin/css/custom_admin.css',)}


# ---------- فایل ملکی ----------
class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 3
    fields = ('image', 'caption', 'order')


class PropertyVideoInline(admin.TabularInline):
    model = PropertyVideo
    extra = 1
    fields = ('video_file', 'video_url', 'poster', 'title', 'order')


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        'property_thumbnail', 'title', 'deal_type', 'usage_type', 'property_type', 'city',
        'status', 'is_featured', 'created_at', 'updated_at',
    )
    list_display_links = ('title',)
    list_filter = ('status', 'deal_type', 'usage_type', 'property_type', 'province', 'city', 'is_featured')
    search_fields = ('title', 'city', 'neighborhood', 'address', 'description')
    list_editable = ('status',)
    date_hierarchy = 'created_at'
    inlines = [PropertyImageInline, PropertyVideoInline]

    fieldsets = (
        ('اطلاعات اصلی', {'fields': ('title', 'status', 'is_featured')}),
        ('دسته‌بندی', {
            'fields': ('deal_type', 'usage_type', 'property_type'),
            'description': 'نوع ملک باید با ترکیب «نوع معامله» و «کاربری» سازگار باشد.'
        }),
        ('موقعیت', {'fields': ('province', 'city', 'neighborhood', 'address')}),
        ('مشخصات', {'fields': ('area', 'bedrooms', 'year_built', 'floor', 'total_floors')}),
        ('ویژگی‌ها و امکانات', {'fields': ('has_elevator', 'has_storage', 'has_parking', 'has_balcony')}),
        ('قیمت — فروش', {'fields': ('price', 'price_per_meter'), 'classes': ('sale-price-group',)}),
        ('قیمت — اجاره', {'fields': ('deposit', 'rent', 'is_convertible'), 'classes': ('rent-price-group',)}),
        ('تماس و توضیحات', {'fields': ('phone', 'description')}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('images')

    @admin.display(description='تصویر')
    def property_thumbnail(self, obj):
        image = obj.main_image
        if not image:
            return format_html(
                '<span class="property-admin-thumbnail-placeholder" aria-label="بدون تصویر">—</span>'
            )
        return format_html(
            '<img class="property-admin-thumbnail" src="{}" alt="تصویر ملک" loading="lazy">',
            image.url,
        )

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        formfield = super().formfield_for_choice_field(db_field, request, **kwargs)
        if db_field.name == 'status' and formfield is not None:
            classes = formfield.widget.attrs.get('class', '').split()
            if 'property-status-select' not in classes:
                classes.append('property-status-select')
            formfield.widget.attrs['class'] = ' '.join(classes)
        return formfield

    class Media:
        js = ('listings/js/property_admin.js',)


# ---------- تنظیمات سایت ----------
@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
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


# ---------- اطلاعات تماس (مرکب: ContactItem + SocialLink) ----------
class ContactItemInline(admin.TabularInline):
    model = ContactItem
    form = ContactItemAdminForm
    extra = 1
    fields = ('item_type', 'label', 'value', 'link', 'order', 'is_active')

    class Media:
        js = ('admin/js/contact_icon_picker.js',)


class SocialLinkInline(admin.TabularInline):
    model = SocialLink
    extra = 1
    fields = ('platform', 'url', 'order', 'is_active')


@admin.register(ContactPage)
class ContactPageAdmin(AdminCSSMixin, admin.ModelAdmin):
    inlines = [ContactItemInline, SocialLinkInline]
    readonly_fields = ('updated_at',)
    fields = ('updated_at',)

    def changelist_view(self, request, extra_context=None):
        obj = ContactPage.load()
        return redirect(reverse('admin:listings_contactpage_change', args=[obj.pk]))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ---------- تیکت‌ها ----------
@admin.register(Ticket)
class TicketAdmin(AdminCSSMixin, admin.ModelAdmin):

    list_display = ('view_button', 'subject', 'name', 'phone', 'status_badge', 'created_at')
    list_display_links = None
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'phone', 'email', 'subject', 'message')
    readonly_fields = ('name', 'phone', 'email', 'subject', 'message', 'created_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('اطلاعات تیکت', {'fields': ('name', 'phone', 'email', 'subject', 'message', 'created_at')}),
        ('مدیریت', {'fields': ('status', 'admin_note')}),
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


# ---------- لاگ‌های سیستم ----------
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

    # Log entries are read-only; deletion is limited to users with the
    # standard admin.delete_logentry permission.
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False

    def log_deletion(self, request, object, object_repr): return
    def log_addition(self, request, object, object_repr): return
    def log_change(self, request, object, message): return

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    @admin.action(description='حذف لاگ‌های قدیمی‌تر از ۳۰ روز', permissions=['delete'])
    def delete_old_logs(self, request, queryset):
        cutoff = timezone.now() - timedelta(days=30)
        deleted, _ = LogEntry.objects.filter(action_time__lt=cutoff).delete()
        self.message_user(request, f'{deleted} لاگ قدیمی حذف شد.', level='success')

    @admin.action(description='حذف لاگ‌های انتخاب‌شده', permissions=['delete'])
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


# ---------- جلسات ----------
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

    # Sessions are read-only; the section checkbox grants view/delete access.
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False

    @admin.action(description='حذف جلسات منقضی‌شده', permissions=['delete'])
    def delete_expired_sessions(self, request, queryset):
        deleted, _ = Session.objects.filter(expire_date__lt=timezone.now()).delete()
        self.message_user(request, f'{deleted} جلسهٔ منقضی حذف شد.', level='success')

    @admin.display(boolean=True, description='منقضی شده')
    def is_expired(self, obj):
        return obj.expire_date < timezone.now()


# ---------- مدیریت مدیران ----------
class UserAdmin(BaseUserAdmin):
    """Manage non-superuser staff accounts; only superusers may enter here."""

    form = ManagerChangeForm
    add_form = ManagerCreationForm
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("دسترسی به بخش‌ها", {"fields": SECTION_PERMISSION_FIELDS}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2"),
        }),
        ("دسترسی به بخش‌ها", {"fields": SECTION_PERMISSION_FIELDS}),
    )
    readonly_fields = ("password",)
    list_display = ("username", "is_active")
    list_display_links = ("username",)
    search_fields = ("username",)
    ordering = ("username",)
    list_filter = ()

    def get_queryset(self, request):
        # This area lists manager accounts only, never superuser/root accounts
        # or ordinary public users.
        return super().get_queryset(request).filter(
            is_staff=True,
            is_superuser=False,
        )

    def save_model(self, request, obj, form, change):
        # Every account created here is an admin staff account, never a superuser.
        obj.is_staff = True
        obj.is_superuser = False
        super().save_model(request, obj, form, change)

        # The checkboxes are the only source of manager permissions.
        # Remove any legacy/group-based grants to avoid hidden extra access.
        obj.groups.clear()
        obj.user_permissions.set(
            permissions_for_sections({
                field_name: form.cleaned_data.get(field_name, False)
                for field_name in SECTION_PERMISSION_FIELDS
            })
        )

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser and (
            obj is None or not obj.is_superuser
        )

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and (
            obj is None or not obj.is_superuser
        )

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser and (
            obj is None or not obj.is_superuser
        )


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, UserAdmin)


# ---------- منوی بخش‌بندی‌شده بر اساس مجوز واقعی ----------
_original_get_app_list = admin.site.get_app_list

_ADMIN_MENU_GROUPS = (
    ("مدیریت مدیران", ("User",)),
    ("فایل‌های ملکی", ("Property",)),
    ("اطلاعات تماس و شبکه‌های اجتماعی", ("ContactPage",)),
    ("تیکت‌ها", ("Ticket",)),
    ("تنظیمات سایت", ("SiteSettings",)),
    ("لاگ‌های سیستم", ("LogEntry",)),
    ("مدیریت نشست‌ها", ("Session",)),
)

_ADMIN_MODEL_LABELS = {
    "User": "مدیران",
    "Property": "فایل‌های ملکی",
    "ContactPage": "اطلاعات تماس",
    "Ticket": "تیکت‌ها",
    "SiteSettings": "تنظیمات سایت",
    "LogEntry": "لاگ‌های سیستم",
    "Session": "نشست‌ها",
}


def _custom_get_app_list(request, app_label=None):
    # Django first filters each model using its real model permissions.
    # We only reorganize the visible models; this does not grant access.
    app_list = _original_get_app_list(request, app_label)
    visible_models = {
        model["object_name"]: model
        for app in app_list
        for model in app["models"]
    }

    grouped_names = set()
    custom_app_list = []

    for index, (section_name, object_names) in enumerate(_ADMIN_MENU_GROUPS):
        models = []
        for object_name in object_names:
            model = visible_models.get(object_name)
            if model is not None:
                model_copy = dict(model)
                model_copy["name"] = _ADMIN_MODEL_LABELS.get(
                    object_name, model_copy["name"]
                )
                models.append(model_copy)
                grouped_names.add(object_name)

        if models:
            custom_app_list.append({
                "name": section_name,
                "app_label": f"admin_section_{index}",
                "app_url": "",
                "has_module_perms": True,
                "models": models,
            })

    # Keep any future registered models visible rather than silently hiding them.
    for app in app_list:
        extras = [
            dict(model)
            for model in app["models"]
            if model["object_name"] not in grouped_names
        ]
        if extras:
            custom_app_list.append({
                "name": app["name"],
                "app_label": app["app_label"],
                "app_url": app["app_url"],
                "has_module_perms": app["has_module_perms"],
                "models": extras,
            })

    return custom_app_list


admin.site.get_app_list = _custom_get_app_list


# ---------- برندینگ پنل ----------
admin.site.site_header = 'پنل مدیریت املاک'
admin.site.site_title = 'مدیریت املاک'
admin.site.index_title = 'به پنل مدیریت خوش آمدید'
