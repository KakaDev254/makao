from django import forms
from django.core.exceptions import ValidationError

from .models import Category, Property


class PropertySubmissionForm(forms.ModelForm):
    """Public submission form. Creates a Property with is_pending=True."""

    class Meta:
        model = Property
        fields = [
            "category",
            "title",
            "description",
            "county",
            "neighborhood",
            "property_type",
            "price",
            "price_period",
            "bedrooms",
            "bathrooms",
            "guests",
            "area_sqft",
            "plot_size",
            "cover_image",
            "agent_name",
            "agent_phone",
        ]
        widgets = {
            "category": forms.Select(attrs={"class": "form-input"}),
            "title": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. 3BR villa in Diani with pool",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-input",
                "rows": 5,
                "placeholder": "Describe the property, its standout features, and the neighborhood.",
            }),
            "county": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. Nairobi, Kwale, Laikipia",
            }),
            "neighborhood": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. Westlands, Diani, Nanyuki",
            }),
            "property_type": forms.Select(attrs={"class": "form-input"}),
            "price": forms.NumberInput(attrs={
                "class": "form-input",
                "placeholder": "Price in KES",
                "min": 0,
            }),
            "price_period": forms.Select(attrs={"class": "form-input"}),
            "bedrooms": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "bathrooms": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "guests": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "area_sqft": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "plot_size": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. 50x100, 1/2 acre",
            }),
            "cover_image": forms.ClearableFileInput(attrs={"class": "form-input"}),
            "agent_name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Your name or agency name",
            }),
            "agent_phone": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. 254712345678",
            }),
        }
        labels = {
            "cover_image": "Main Cover Image",
            "agent_phone": "Contact phone",
        }
        help_texts = {
            "agent_phone": "Include country code, no spaces. E.g. 254712345678",
            "price": "Number only, in Kenyan Shillings.",
            "cover_image": "This is the primary image shown on cards.",
        }

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price <= 0:
            raise ValidationError("Enter a price greater than zero.")
        return price

    def clean_agent_phone(self):
        phone = self.cleaned_data.get("agent_phone", "")
        digits = "".join(ch for ch in phone if ch.isdigit())
        if len(digits) < 9:
            raise ValidationError("Enter a valid phone number with country code.")
        return digits