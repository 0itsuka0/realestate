from django import forms

from .models import Ticket


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
