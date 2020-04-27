from django_countries.fields import CountryField
from django import forms
from django_countries.widgets import CountrySelectWidget


PAYMENT_OPTIONS = (
    ('P', 'PayPal (currently unavailable: will redirect to stripe)'),
    ('S', 'Stripe')
)


class CheckoutForm(forms.Form):
    address = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': '1234 Main St'
    }))
    address2 = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Apartment or suite'}))
    country = CountryField(blank_label='(select country)').formfield(
        widget=CountrySelectWidget(attrs={
            'class': 'custom-select d-block w-100'
        }))
    zip = forms.CharField(widget=forms.TextInput({
        'class': 'form-control',
        'placeholder': '89381-6757'
    }))
    same_shipping_address = forms.BooleanField(required=False)
    save_info = forms.BooleanField(required=False)
    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect, choices=PAYMENT_OPTIONS)


class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',
                                                         'placeholder': 'Promo code',
                                                         'aria-label': 'Recipient\'s username',
                                                         'aria-describedby': 'basic-addon2'}))
