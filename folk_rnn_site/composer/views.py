from django.shortcuts import redirect, render

from composer.models import Tune

def composer_page(request):
    if request.method == 'POST':
        tune = Tune()
        tune.seed = request.POST['seed_text']
        tune.save()
        return redirect('/candidate-tune/{}'.format(tune.id))
        
    return render(request, 'compose.html')

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
