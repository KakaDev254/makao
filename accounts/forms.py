from django import forms
from django.contrib.auth.models import User

from .models import Profile


class UserForm(forms.ModelForm):
    """Base User fields: first name, last name, email."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-input",
            "placeholder": "you@example.com",
            "autocomplete": "email",
        }),
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "First name",
                "autocomplete": "given-name",
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Last name",
                "autocomplete": "family-name",
            }),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Another account already uses this email.")
        return email


class ProfileForm(forms.ModelForm):
    """Extended Profile fields: display name, avatar, contact, notifications."""

    class Meta:
        model = Profile
        fields = (
            "display_name",
            "avatar",
            "phone",
            "county",
            "bio",
            "notify_email_on_inquiry",
            "notify_price_drops",
            "notify_new_listings",
        )
        widgets = {
            "display_name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. Jane Mwangi",
            }),
            "avatar": forms.ClearableFileInput(attrs={"class": "form-input"}),
            "phone": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "254712345678",
                "autocomplete": "tel",
            }),
            "county": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. Nairobi",
            }),
            "bio": forms.Textarea(attrs={
                "class": "form-input",
                "rows": 3,
                "placeholder": "A short line about yourself (optional)",
                "maxlength": 280,
            }),
        }
        help_texts = {
            "display_name": "Shown across Makao instead of your full name.",
            "phone": "Include country code, no spaces. E.g. 254712345678",
            "bio": "Max 280 characters.",
        }

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        digits = "".join(ch for ch in phone if ch.isdigit())
        if phone and len(digits) < 9:
            raise forms.ValidationError("Enter a valid phone with country code.")
        return digits


class DeleteAccountForm(forms.Form):
    """Confirm account deletion."""

    confirm = forms.CharField(
        label="Type DELETE to confirm",
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "DELETE",
            "autocomplete": "off",
        }),
    )

    def clean_confirm(self):
        value = self.cleaned_data.get("confirm", "").strip()
        if value != "DELETE":
            raise forms.ValidationError("Type DELETE (all caps) to confirm.")
        return value