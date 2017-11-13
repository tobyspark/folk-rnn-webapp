from django import forms

class ComposeForm(forms.Form):
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
    seed = forms.CharField(label='Seed:', 
                           widget=forms.TextInput(attrs={'placeholder':'Enter start of tune in ABC notation'}),
                           required=False)

    