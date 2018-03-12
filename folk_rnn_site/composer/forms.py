from django import forms
from django.core.exceptions import ValidationError
from random import randint

from composer.rnn_models import choices as rnn_choices
from composer.rnn_models import validate_tokens, validate_meter, validate_key

class ChoiceFieldNoValidation(forms.ChoiceField):
    def validate(self, value):
        pass

class ComposeForm(forms.Form):
    model = forms.ChoiceField(label='RNN Model:', choices=rnn_choices())
    temp = forms.DecimalField(label='RNN Temperature:', min_value=0.01, max_value=10, decimal_places=2, initial=1)
    seed = forms.IntegerField(label='RNN Seed:', min_value=0, max_value=2**15, initial=lambda : randint(0, 2**15))
    meter = ChoiceFieldNoValidation(label='Meter:', choices=())
    key = ChoiceFieldNoValidation(label='Key:', choices=())
    start_abc = forms.CharField(label='Prime tokens:', 
                           widget=forms.Textarea(),
                           error_messages={'invalid': 'Invalid ABC notation as per the RNN model'},
                           required=False)

    # Validate whole form as validation (might) depend on particular model
    def clean(self):
        super(ComposeForm, self).clean()
        
        if self.cleaned_data['start_abc']:
            tokens = self.cleaned_data['start_abc'].split(' ')
            if not validate_tokens(tokens, model_file_name=self.cleaned_data['model']):
                self.add_error('start_abc', ValidationError('Invalid ABC as per RNN model', code='invalid'))
        
        if 'meter' in self.data:
            if validate_meter(self.data['meter'], model_file_name=self.cleaned_data['model']):
                self.cleaned_data['meter'] = self.data['meter']
            else:
                self.add_error('meter', ValidationError('Invalid meter as per RNN model', code='invalid'))
        else:
            self.cleaned_data['meter'] = ''
        
        if 'key' in self.data:
            if validate_key(self.data['key'], model_file_name=self.cleaned_data['model']):
                self.cleaned_data['key'] = self.data['key']
            else:
                self.add_error('key', ValidationError('Invalid key as per RNN model', code='invalid'))
        else:
            self.cleaned_data['key'] = ''
class ArchiveForm(forms.Form):
    title = forms.CharField(label='Name your tune:')
    