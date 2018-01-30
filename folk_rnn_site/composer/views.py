from django.shortcuts import redirect, render
from channels import Channel

from composer.models import RNNTune
from composer.forms import ComposeForm


def home_page(request):
    if request.method == 'POST':
        form = ComposeForm(request.POST)
        if form.is_valid():
            tune = RNNTune()
            tune.rnn_model_name = form.cleaned_data['model']
            tune.seed = form.cleaned_data['seed']
            tune.temp = form.cleaned_data['temp']
            tune.prime_tokens = '{} {}'.format(
                                form.cleaned_data['meter'],
                                form.cleaned_data['key'], 
                                )
            if form.cleaned_data['prime_tokens']:
                tune.prime_tokens += ' {}'.format(form.cleaned_data['prime_tokens'])
            tune.save()
            Channel('folk_rnn').send({'id': tune.id})
            return redirect('/tune/{}'.format(tune.id))
    else:
        form = ComposeForm()
    
    return render(request, 'composer/home.html', {
                                'form': form,
                                })

def tune_page(request, tune_id=None):
    try:
        tune_id_int = int(tune_id)
        tune = RNNTune.objects.get(id=tune_id_int)
    except (TypeError, RNNTune.DoesNotExist):
        return redirect('/')

    # Handle rnn-in-process

    if not tune.rnn_started:
        return render(request, 'composer/tune-in-process.html', {
            'prime_tokens': tune.prime_tokens,
            'rnn_has_started': False,
            'candidate_id': tune_id_int,
            })

    if not tune.rnn_finished:
        return render(request, 'composer/tune-in-process.html', {
            'prime_tokens': tune.prime_tokens,
            'rnn_has_started': True,
            'candidate_id': tune_id_int,
            })
            
    # Display generated tune

    tune_lines = tune.abc.split('\n')

    return render(request, 'composer/tune.html', {
        'tune': tune,
        'rnn_duration': (tune.rnn_finished - tune.rnn_started).total_seconds(),
        'tune_cols': max(len(line) for line in tune_lines), # TODO: look into autosize via CSS, when CSS is a thing round here.
        'tune_rows': len(tune_lines),
        })