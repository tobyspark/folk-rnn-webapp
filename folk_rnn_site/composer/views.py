from django.shortcuts import redirect, render

from composer.models import CandidateTune
from composer.forms import ComposeForm, CandidateForm

def composer_page(request):
    if request.method == 'POST':
        form = ComposeForm(request.POST)
        if form.is_valid():
            tune = CandidateTune()
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
            return redirect('/candidate-tune/{}'.format(tune.id))
    else:
        form = ComposeForm()
    
    return render(request, 'compose.html', {'form': form})

def candidate_tune_page(request, tune_id=None):
    try:
        tune_id_int = int(tune_id)
        tune = CandidateTune.objects.get(id=tune_id_int)
    except (TypeError, CandidateTune.DoesNotExist):
        return redirect('/')
    
    if not tune.rnn_started:
        return render(request, 'candidate-tune-in-process.html', {
            'prime_tokens': tune.prime_tokens,
            'rnn_has_started': False,
            })
    
    if not tune.rnn_finished:
        return render(request, 'candidate-tune-in-process.html', {
            'prime_tokens': tune.prime_tokens,
            'rnn_has_started': True,
            })
    
    show_user = True
    if request.method == 'POST':
        form = CandidateForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['edit_state'] == 'user':
                tune.user_tune = form.cleaned_data['tune']
                tune.save()
            if form.cleaned_data['edit'] == 'rnn':
                show_user = False
    if show_user:
        form = CandidateForm({
                    'tune': tune.user_tune if tune.user_tune else tune.rnn_tune,
                    'edit': 'user',
                    'edit_state': 'user',
                    })
    else:
        form = CandidateForm({
                    'tune': tune.rnn_tune,
                    'edit': 'rnn',
                    'edit_state': 'rnn',
                    })
        form.fields['tune'].widget.attrs['readonly'] = True

    return render(request, 'candidate-tune.html', {
        'model': tune.rnn_model_name,
        'seed': tune.seed,
        'temp': tune.temp,
        'prime_tokens': tune.prime_tokens,
        'requested': tune.requested,
        'rnn_duration': (tune.rnn_finished - tune.rnn_started).total_seconds(),
        'form': form,
        'show_user': show_user,
        })
