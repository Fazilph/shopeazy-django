
from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order  # Specify the model for the form
        fields = ['first_name', 'last_name', 'phone', 'email', 'address_line_1', 'address_line_2', 'country', 'state', 'city', 'order_note']
