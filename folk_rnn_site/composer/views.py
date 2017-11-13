from django.shortcuts import redirect, render

from composer.models import Tune
from composer.forms import ComposeForm

# FIXME: Write a ABC validator per model used, ie. all(x in token2idx[y])
def validate_seed(seed):
    return len(seed) > 0

def composer_page(request):
    if request.method == 'POST':
        form = ComposeForm(request.POST)
        if form.is_valid():
            tune = Tune()
            tune.rnn_model_name = form.cleaned_data['model']
            tune.seed = '{} {}'.format(
                                form.cleaned_data['meter'],
                                form.cleaned_data['key'], 
                                )
            if validate_seed(form.cleaned_data['seed']):
                tune.seed += ' {}'.format(form.cleaned_data['seed'])
            tune.save()
            return redirect('/candidate-tune/{}'.format(tune.id))
    
    form = ComposeForm()    
    return render(request, 'compose.html', {'form': form})

def candidate_tune_page(request, tune_id=None):
    try:
        tune_id_int = int(tune_id)
        tune = Tune.objects.get(id=tune_id_int)
    except (TypeError, Tune.DoesNotExist):
        return redirect('/')
    
    if not tune.rnn_started:
        return render(request, 'candidate-tune-in-process.html', {
            'seed': tune.seed,
            'rnn_has_started': False,
            })
    
    if not tune.rnn_finished:
        return render(request, 'candidate-tune-in-process.html', {
            'seed': tune.seed,
            'rnn_has_started': True,
            })
    
    return render(request, 'candidate-tune.html', {
        'seed': tune.seed,
        'tune': tune.rnn_tune,
        'requested': tune.requested,
        'rnn_duration': (tune.rnn_finished - tune.rnn_started).total_seconds(),
        })
