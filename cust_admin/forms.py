from django import forms
from store.models import *
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date

class ProductVariantAssignForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        empty_label="Select Product",
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )
    size = forms.ModelChoiceField(
        queryset=Size.objects.all(),
        empty_label="Select Size",
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )
    price = forms.DecimalField(
        decimal_places=2,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Price', 'required': True})
    )
    old_price = forms.DecimalField(
        decimal_places=2,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Old Price', 'required': True})
    )
    stock = forms.IntegerField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Stock', 'required': True})
    )
    in_stock = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    status = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        initial_data = kwargs.pop('initial_data', None)
        super().__init__(*args, **kwargs)
        if initial_data:
            for field, value in initial_data.items():
                if field in self.fields:
                    self.fields[field].initial = value