from django import forms
from django.core.exceptions import ValidationError
from random import randint

from composer.rnn_models import choices as rnn_choices
from composer.rnn_models import validate_tokens

class ComposeForm(forms.Form):
    model = forms.ChoiceField(label='RNN Model:', choices=rnn_choices())
    temp = forms.DecimalField(label='RNN Temperature:', min_value=0.01, max_value=10, decimal_places=2, initial=1)
    seed = forms.IntegerField(label='RNN Seed:', min_value=0, max_value=2**15, initial=lambda : randint(0, 2**15))
    meter = forms.ChoiceField(label='Meter:', choices=(
                                                    ('M:4/4', '4/4'), 
                                                    ('M:6/8', '6/8'), 
                                                    ('M:9/8', '9/8'), 
                                                    ('M:2/4', '2/4'), 
                                                    ('M:3/4', '3/4'), 
                                                    ('M:12/8', '12/8'),
                                                    ))
    key = forms.ChoiceField(label='Key:', choices=(
                                                ('K:Cmaj', 'C Major'),
                                                ('K:Cmin', 'C Minor'),
                                                ('K:Cdor', 'C Dorian'),
                                                ('K:Cmix', 'C Mixolydian'),
                                                ))
    prime_tokens = forms.CharField(label='Prime tokens:', 
                           widget=forms.TextInput(attrs={'placeholder':'Enter start of tune in ABC notation'}),
                           error_messages={'invalid': 'Invalid ABC notation as per the RNN model'},
                           required=False)

    # Validate whole form as prime_tokens validation (might) depend on particular model
    def clean(self):
        super(ComposeForm, self).clean()
        if self.cleaned_data['prime_tokens']:
            tokens = self.cleaned_data['prime_tokens'].split(' ')
            if not validate_tokens(tokens, model_file_name=self.cleaned_data['model']):
                self.add_error('prime_tokens', ValidationError('Invalid ABC as per RNN model', code='invalid'))

class ArchiveForm(forms.Form):
    title = forms.CharField(label='Name your tune:')
    folkrnn_id = forms.IntegerField(widget=forms.HiddenInput)
    