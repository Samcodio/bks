from django import forms
from app.models import User
from django.core.validators import RegexValidator
import re


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password',
                               widget=forms.PasswordInput(
                                   attrs={
                                       'class': 'form-control',
                                       'autofocus': 'true',
                                       'type': 'password',
                                       'required': 'true',
                                       'placeholder': 'Mich@retro31',
                                       'autocomplete': 'off',
                                       'id': 'password1'

                                   }
                               ))
    confirm_password = forms.CharField(label='Confirm Password',
                                       widget=forms.PasswordInput(
                                           attrs={
                                               'class': 'form-control',
                                               'autofocus': 'true',
                                               'type': 'password',
                                               'required': 'true',
                                               'placeholder': 'Re-enter Password',
                                               'id': 'password2',
                                               'autocomplete': 'off'
                                           }
                                       ))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'social_sec')
        widgets = {
            'username': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'autofocus': 'true',
                    'type': 'text',
                    'required': 'true',
                    'placeholder': 'user ID',
                    'autocomplete': 'off'
                }
            ),
            'first_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'autofocus': 'true',
                    'type': 'text',
                    'required': 'true',
                    'placeholder': 'First Legal Name',
                    'autocomplete': 'off'
                }
            ),
            'last_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'autofocus': 'true',
                    'type': 'text',
                    'required': 'true',
                    'placeholder': 'Last Legal Name',
                    'autocomplete': 'off'
                }
            ),
            'email': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'autofocus': 'true',
                    'type': 'email',
                    'required': 'true',
                    'placeholder': 'name@example.com',
                    'autocomplete': 'off'
                }
            ),
            'social_sec': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'autofocus': 'true',
                    'type': 'text',
                    'required': 'true',
                    'style': 'padding-left: 40px;',
                    'placeholder': 'XXX-XX-XXXX',
                    'maxlength': '11',
                    'inputmode': 'numeric',
                    'autocomplete': 'off'
                }
            ),
        }

    def clean_social_sec(self):
        """Validate SSN format and store digits only."""
        ssn = self.cleaned_data.get('social_sec', '')

        # Strip everything except digits
        digits_only = re.sub(r'\D', '', ssn)

        # Validate exactly 9 digits
        if len(digits_only) != 9:
            raise forms.ValidationError("SSN must be exactly 9 digits.")

        # Validate no invalid patterns (e.g., all zeros in any section)
        if re.match(r'^000|000$|00\d{4}$', digits_only):
            raise forms.ValidationError("Invalid SSN format.")

        # Return digits only for storage (no hyphens in database)
        return digits_only

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if len(password) < 8:
            raise forms.ValidationError(
                "Password must be at least 8 characters long."
            )

        if not re.search(r"[A-Z]", password):
            raise forms.ValidationError(
                "Password must contain at least one uppercase letter."
            )

        if not re.search(r"[a-z]", password):
            raise forms.ValidationError(
                "Password must contain at least one lowercase letter."
            )

        if not re.search(r"[0-9]", password):
            raise forms.ValidationError(
                "Password must contain at least one number."
            )

        return password

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                self.add_error(
                    "confirm_password",
                    "Passwords do not match"
                )
        return cleaned_data

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user