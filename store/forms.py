from django import forms


class CheckoutForm(forms.Form):
    address = forms.CharField(widget=forms.Textarea, required=True)
    is_emergency_delivery = forms.BooleanField(required=False)
