from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import User
from django.templatetags.static import static

from .admin_permissions import SECTION_PERMISSION_FIELDS, SECTION_PERMISSION_RULES, section_permission_strings
from .models import ContactItem, Ticket


class ManagerPermissionsFormMixin:
    """Set the initial state of the section checkboxes from Django permissions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            granted_permissions = self.instance.get_all_permissions()
            for field_name in SECTION_PERMISSION_FIELDS:
                required = set(section_permission_strings(field_name))
                self.initial[field_name] = required.issubset(granted_permissions)


class ManagerCreationForm(ManagerPermissionsFormMixin, UserCreationForm):
    """Minimal form for creating a staff manager account."""

    can_manage_properties = forms.BooleanField(
        label=SECTION_PERMISSION_RULES["can_manage_properties"]["label"], required=False
    )
    can_manage_contact = forms.BooleanField(
        label=SECTION_PERMISSION_RULES["can_manage_contact"]["label"], required=False
    )
    can_manage_tickets = forms.BooleanField(
        label=SECTION_PERMISSION_RULES["can_manage_tickets"]["label"], required=False
    )
    can_manage_site_settings = forms.BooleanField(
        label=SECTION_PERMISSION_RULES["can_manage_site_settings"]["label"], required=False
    )
    can_view_logs = forms.BooleanField(
        label=SECTION_PERMISSION_RULES["can_view_logs"]["label"], required=False
    )
    can_manage_sessions = forms.BooleanField(
        label=SECTION_PERMISSION_RULES["can_manage_sessions"]["label"], required=False
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)


class ManagerChangeForm(ManagerPermissionsFormMixin, UserChangeForm):
    """Minimal form for editing a manager and its section permissions."""

    can_manage_properties = forms.BooleanField(
        label=SECTION_PERMISSION_RULES["can_manage_properties"]["label"], required=False
    )
    can_manage_contact = forms.BooleanField(
        label=SECTION_PERMISSION_RULES["can_manage_contact"]["label"], required=False
    )
    can_manage_tickets = forms.BooleanField(
        label=SECTION_PERMISSION_RULES["can_manage_tickets"]["label"], required=False
    )
    can_manage_site_settings = forms.BooleanField(
        label=SECTION_PERMISSION_RULES["can_manage_site_settings"]["label"], required=False
    )
    can_view_logs = forms.BooleanField(
        label=SECTION_PERMISSION_RULES["can_view_logs"]["label"], required=False
    )
    can_manage_sessions = forms.BooleanField(
        label=SECTION_PERMISSION_RULES["can_manage_sessions"]["label"], required=False
    )

    class Meta(UserChangeForm.Meta):
        model = User
        fields = ("username", "password")


class ContactIconSelect(forms.Select):
    """A normal select enhanced by local SVG icon buttons in the admin."""

    def __init__(self, attrs=None, choices=()):
        widget_attrs = {
            "class": "contact-icon-select",
            "data-icon-sprite": static("images/contact-icons.svg"),
        }
        widget_attrs.update(attrs or {})
        super().__init__(attrs=widget_attrs, choices=choices)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option_attrs = dict(attrs or {})
        if value not in (None, ""):
            option_attrs["data-icon"] = str(value)
        return super().create_option(
            name, value, label, selected, index,
            subindex=subindex, attrs=option_attrs,
        )


class ContactItemAdminForm(forms.ModelForm):
    """Use a searchable visual icon palette for each contact item."""

    class Meta:
        model = ContactItem
        fields = "__all__"
        widgets = {
            "item_type": ContactIconSelect,
        }


class OwnerAccountForm(forms.ModelForm):
    """Allow the site owner to edit only their username and email."""

    class Meta:
        model = User
        fields = ("username", "email")
        labels = {
            "username": "نام کاربری",
            "email": "ایمیل",
        }
        widgets = {
            "username": forms.TextInput(attrs={"class": "vTextField", "autocomplete": "username"}),
            "email": forms.EmailInput(attrs={"class": "vTextField", "autocomplete": "email"}),
        }

class TicketForm(forms.ModelForm):
    """Validated public contact form backed by the Ticket model."""

    class Meta:
        model = Ticket
        fields = ("name", "phone", "email", "subject", "message")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "autocomplete": "name"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "type": "tel", "autocomplete": "tel"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }

    def clean_name(self):
        value = self.cleaned_data["name"].strip()
        if not value:
            raise forms.ValidationError("وارد کردن نام الزامی است.")
        return value

    def clean_phone(self):
        value = self.cleaned_data["phone"].strip()
        if not value:
            raise forms.ValidationError("وارد کردن شماره تماس الزامی است.")
        return value

    def clean_subject(self):
        value = self.cleaned_data["subject"].strip()
        if not value:
            raise forms.ValidationError("وارد کردن موضوع الزامی است.")
        return value

    def clean_message(self):
        value = self.cleaned_data["message"].strip()
        if not value:
            raise forms.ValidationError("وارد کردن پیام الزامی است.")
        return value
