from django.shortcuts import redirect, render
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django_hosts.resolvers import reverse

from composer.models import RNNTune
from composer.forms import ComposeForm, ArchiveForm

from archiver.models import Tune

def home_page(request):
    if request.method == 'POST':
        form = ComposeForm(request.POST)
        if form.is_valid():
            tune = RNNTune()
            tune.rnn_model_name = form.cleaned_data['model']
            tune.seed = form.cleaned_data['seed']
            tune.temp = form.cleaned_data['temp']
            tune.meter = form.cleaned_data['meter']
            tune.key = form.cleaned_data['key']
            tune.start_abc = form.cleaned_data['prime_tokens']
            tune.save()
            
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.send)('folk_rnn', {
                                                    'type': 'folkrnn.generate', 
                                                    'id': tune.id
                                                    })
            return redirect('/tune/{}'.format(tune.id))
    else:
        form = ComposeForm()
    
    return render(request, 'composer/home.html', {
                                'compose_form': form,
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
            'compose_form': ComposeForm(),
            })

    if not tune.rnn_finished:
        return render(request, 'composer/tune-in-process.html', {
            'prime_tokens': tune.prime_tokens,
            'rnn_has_started': True,
            'candidate_id': tune_id_int,
            'compose_form': ComposeForm(),
            })
            
    # Display generated tune

    return render(request, 'composer/tune.html', {
        'tune': tune,
        'archive_form': ArchiveForm({'folkrnn_id': tune_id_int, 'title': tune.title}),
        'rnn_duration': (tune.rnn_finished - tune.rnn_started).total_seconds(),
        'tune_rows': tune.abc.count('\n'),
        'compose_form': ComposeForm(),
        'machine_folk_tune_count': Tune.objects.count()
        })

def archive_tune(request, tune_id=None):
    try:
        tune_id_int = int(tune_id)
        tune = RNNTune.objects.get(id=tune_id_int)
    except (TypeError, RNNTune.DoesNotExist):
        return redirect('/')
        
    if request.method == 'POST':
        form = ArchiveForm(request.POST)
        if form.is_valid():
            try:
                tune_in_archive = Tune.objects.get(rnn_tune=tune)
            except Tune.DoesNotExist:
                tune_in_archive = Tune(rnn_tune=tune, abc_rnn=tune.abc)  
                tune_in_archive.title = form.cleaned_data['title']          
                tune_in_archive.save()
            return redirect(reverse('tune', host='archiver', kwargs={'tune_id': tune_in_archive.id}))
    return redirect('/')