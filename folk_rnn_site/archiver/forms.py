from django import forms

class SettingForm(forms.Form):
    abc = forms.CharField(label='', widget=forms.Textarea(attrs={'id': 'abc'}))
    
class CommentForm(forms.Form):
    text = forms.CharField(label='Comment:', widget=forms.Textarea(attrs={'id': 'new_comment'}))
    
class SignupForm(forms.Form):
    name = forms.CharField(label='Name:')
    password = forms.CharField(label='Password:', widget=forms.PasswordInput())
    email = forms.EmailField(label='Email:')