from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms.extras.widgets import SelectDateWidget
from registration import validators
from embed_video.fields import EmbedVideoFormField

from folk_rnn_site.models import conform_abc
from archiver import YEAR_CHOICES
from archiver.models import User, Tune, TuneAttribution, Setting

class AttributionForm(forms.Form):
    text = forms.CharField(required=False)
    url = forms.URLField(required=False)
        
class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        fields = ['abc']
        widgets = {
            'abc': forms.Textarea(attrs={'id': 'abc'})
        }
    
class CommentForm(forms.Form):
    text = forms.CharField(label='Comment:', widget=forms.Textarea(attrs={'id': 'new_comment'}))
    
class ContactForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea())
    email = forms.EmailField(required=False)

class TuneForm(forms.ModelForm):
    class Meta:
        model = Tune
        fields = ['abc']        
        # abc = forms.CharField(widget=forms.Textarea())
        # text = forms.CharField(widget=forms.Textarea())
        # url = forms.URLField(required=False)

class TuneAttributionForm(forms.ModelForm):
    class Meta:
        model = TuneAttribution
        fields = ['text', 'url']

class RecordingForm(forms.Form):
    title = forms.CharField()
    body = forms.CharField(widget=forms.Textarea())
    date = forms.DateField(widget=SelectDateWidget(years=YEAR_CHOICES))
    url = EmbedVideoFormField()

class EventForm(forms.Form):
    title = forms.CharField()
    body = forms.CharField(widget=forms.Textarea())
    date = forms.DateField(widget=SelectDateWidget(years=YEAR_CHOICES))

class TunebookForm(forms.Form):
    add = forms.BooleanField(required=False)

class SearchForm(forms.Form):
    search = forms.CharField(required=False)

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

