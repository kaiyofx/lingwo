from django import forms
from .models import ABSUser

class OTPTokenForm(forms.Form):
    user_email = forms.EmailField(
        required=False,
        max_length=ABSUser._meta.get_field('email').max_length
    )

    username = forms.CharField(
        max_length=ABSUser._meta.get_field('username').max_length,
        required=False
    )
    
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        required=False
    )

    # *Опционально:* Вы можете добавить метод clean_grant_type для дополнительной валидации
    def clean_grant_type(self):
        grant_type = self.cleaned_data.get('grant_type')
        if grant_type != 'otp':
            raise forms.ValidationError("Grant type must be 'otp'.")
        return grant_type