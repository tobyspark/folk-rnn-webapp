from django import forms

class SettingForm(forms.Form):
    abc = forms.CharField(label='', widget=forms.Textarea(attrs={'id': 'abc'}))
    
class CommentForm(forms.Form):
    text = forms.CharField(label='Comment:', widget=forms.Textarea(attrs={'id': 'new_comment'}))
    
class SignupForm(forms.Form):
    first_name = forms.CharField(label='First name:')
    last_name = forms.CharField(label='Last name:')
    password = forms.CharField(label='Password:', widget=forms.PasswordInput())
    email = forms.EmailField(label='Email:')