from django import forms

class TuneForm(forms.Form):
    tune = forms.CharField(label='', widget=forms.Textarea(attrs={'id': 'abc'}))
    edit = forms.ChoiceField(label='', 
                            widget=forms.RadioSelect(attrs={'onchange': 'this.form.submit();'}), 
                            choices=(
                                ('rnn', 'RNN original'),
                                ('user', 'Your setting'),
                                ))
    edit_state = forms.ChoiceField(widget=forms.HiddenInput,
                            choices=(
                                ('rnn', ''),
                                ('user', ''),
                                ))

class CommentForm(forms.Form):
    text = forms.CharField(label='Comment:', widget=forms.Textarea(attrs={'id': 'new_comment'}))
    author = forms.CharField(label='Author:', widget=forms.TextInput(attrs={'id': 'new_comment_author'}))
    
class SignupForm(forms.Form):
    name = forms.CharField(label='Name:')
    password = forms.CharField(label='Password:', widget=forms.PasswordInput())
    email = forms.EmailField(label='Email:')