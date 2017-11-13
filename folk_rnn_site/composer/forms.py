from django import forms

class ComposeForm(forms.Form):
                           widget=forms.TextInput(attrs={'placeholder':'Enter start of tune in ABC notation'}),
                           required=False)
