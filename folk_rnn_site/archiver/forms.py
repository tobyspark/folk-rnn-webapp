from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms.extras.widgets import SelectDateWidget
from django_registration import validators
from embed_video.fields import EmbedVideoFormField

from folk_rnn_site.models import conform_abc
from archiver import YEAR_CHOICES
from archiver.models import User, Tune, TuneAttribution, Setting

class SettingForm(forms.ModelForm):
    """
    User input to create a Setting
    """
    class Meta:
        model = Setting
        fields = ['abc', 'check_valid_abc']
    
class CommentForm(forms.Form):
    """
    User input to create a Comment
    """
    text = forms.CharField(label='Comment:', widget=forms.Textarea(attrs={'id': 'new_comment'}))
    
class ContactForm(forms.Form):
    """
    For sending a message to site admins
    """
    text = forms.CharField(widget=forms.Textarea())
    email = forms.EmailField(required=False)

class TuneForm(forms.ModelForm):
    """
    User input to create a Tune
    """
    class Meta:
        model = Tune
        fields = ['abc', 'check_valid_abc']        

class TuneAttributionForm(forms.ModelForm):
    """
    User input to create a TuneAttribution
    """
    class Meta:
        model = TuneAttribution
        fields = ['text', 'url']

class RecordingForm(forms.Form):
    """
    User input to create a Recording
    """
    title = forms.CharField()
    body = forms.CharField(widget=forms.Textarea())
    date = forms.DateField(widget=SelectDateWidget(years=YEAR_CHOICES))
    url = EmbedVideoFormField()

class EventForm(forms.Form):
    """
    User input to create an Event
    """
    title = forms.CharField()
    body = forms.CharField(widget=forms.Textarea())
    date = forms.DateField(widget=SelectDateWidget(years=YEAR_CHOICES))

class TunebookForm(forms.Form):
    """
    User input for 'In your tunebook:'
    """
    add = forms.BooleanField(required=False)

class SearchForm(forms.Form):
    """
    User input for search field
    """
    search = forms.CharField(required=False)

class VoteForm(forms.Form):
    """
    User input to vote upon something
    """
    object_id = forms.IntegerField(widget=forms.HiddenInput)

def validate_duplicate_email(value):
    """
    Raise if value is an existing email address
    """
    if User.objects.filter(email__iexact=value):
        raise forms.ValidationError(validators.DUPLICATE_EMAIL, code='invalid')

class RegistrationForm(UserCreationForm):
    """
    User input for sign-up
    As per registration docs, this should be a minimal subclass of registration.forms.RegistrationFormUniqueEmail.
    However that wasn't working, so this instead is an equivalent, based on some of that code.
    """
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

