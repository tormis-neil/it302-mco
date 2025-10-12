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
    contact_name = forms.CharField(max_length=120)
    contact_phone = forms.CharField(
        max_length=20,
        required=False,
        validators=[
            RegexValidator(r"^[0-9+()\-\s]*$", "Enter a valid phone number."),
        ],
    )
    special_instructions = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"dashboard-input {classes}".strip()