"""Forms powering the cart and checkout experience."""
from __future__ import annotations

from django import forms
from django.core.validators import RegexValidator

from menu.models import MenuItem


class CartAddForm(forms.Form):
    menu_item = forms.ModelChoiceField(
        queryset=MenuItem.objects.filter(is_available=True),
        widget=forms.HiddenInput,
    )
    quantity = forms.IntegerField(min_value=1, max_value=10, initial=1)


class CartUpdateForm(forms.Form):
    quantity = forms.IntegerField(min_value=0, max_value=10)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quantity"].widget.attrs.update({
            "class": "cart-quantity-input",
            "min": 0,
            "max": 10,
        })


class CheckoutForm(forms.Form):
    """
    Form for checkout contact information.

    Fields:
    - contact_name: Customer name (required, min 2 chars)
    - contact_phone: Phone number (required, validated format)
    - special_instructions: Optional order notes
    """
    contact_name = forms.CharField(
        max_length=120,
        min_length=2,
        error_messages={
            'required': 'Contact name is required.',
            'min_length': 'Contact name must be at least 2 characters.',
        }
    )
    contact_phone = forms.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                r"^[0-9+()\-\s]{7,20}$",
                "Enter a valid phone number (7-20 digits, may include +, -, spaces)."
            ),
        ],
        error_messages={
            'required': 'Contact phone is required.',
        }
    )
    special_instructions = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        max_length=500,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"dashboard-input {classes}".strip()