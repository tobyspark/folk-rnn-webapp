import json
from django.shortcuts import redirect, render
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django_hosts.resolvers import reverse

from composer.models import RNNTune
from composer.forms import ComposeForm, ArchiveForm

from archiver.models import Tune

def home_page(request):
    return render(request, 'composer/home.html', {
                                'compose_form': ComposeForm(),
                                'archive_form': ArchiveForm(),
                                'machine_folk_tune_count': Tune.objects.count(),
                                })

def tune_page(request, tune_id=None):
    try:
        tune_id_int = int(tune_id)
        tune = RNNTune.objects.get(id=tune_id_int)
    except (TypeError, RNNTune.DoesNotExist):
        return redirect('/')

    return render(request, 'composer/home.html', {
        'compose_form': ComposeForm(),
        'archive_form': ArchiveForm(),
        'machine_folk_tune_count': Tune.objects.count(),
        'tune_id': tune.id,
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