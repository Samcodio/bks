from .models import *
from django.forms import *
from django.contrib.auth.forms import SetPasswordForm

class ChangePasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.fields['new_password1'].widget = PasswordInput(
            attrs={
                "class": "form-control mb-1",
                "required": "true",
                "placeholder": "New Password...",
                "autocomplete": "off"
            }
        )
        self.fields['new_password2'].widget = PasswordInput(
            attrs={
                "class": "form-control",
                "required": "true",
                "placeholder": "Confirm Password...",
                "autocomplete": "off"
            }
        )