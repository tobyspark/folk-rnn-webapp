from django import forms
from django.contrib.auth.forms import UserCreationForm
from registration import validators

from archiver.models import User

class SettingForm(forms.Form):
    abc = forms.CharField(label='', widget=forms.Textarea(attrs={'id': 'abc'}))
    
class CommentForm(forms.Form):
    text = forms.CharField(label='Comment:', widget=forms.Textarea(attrs={'id': 'new_comment'}))
    

# As per registration docs, this should subclass registration.forms.RegistrationFormUniqueEmail.
# That wasn't working, so here instead is an equivalent, based on some of that code.
def validate_duplicate_email(value):
    if User.objects.filter(email__iexact=value):
        raise forms.ValidationError(validators.DUPLICATE_EMAIL, code='invalid')

class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'email',
            'first_name',
            'last_name',
            'password1',
            'password2'
        ]
    
    email = forms.EmailField(
        label='Email address:',
        required=True,
        validators=[
            validate_duplicate_email,
            validators.validate_confusables_email,
        ]
    )
    first_name = forms.CharField(
        label='First name:',
        required='True',
        validators=[
            validators.ReservedNameValidator(),
            validators.validate_confusables,
        ]
    )
    last_name = forms.CharField(
        label='Last name:',
        required='True',
        validators=[
            validators.ReservedNameValidator(),
            validators.validate_confusables,
        ]
    )

