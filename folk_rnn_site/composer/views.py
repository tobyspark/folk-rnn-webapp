import json
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.core.files import File as dFile
from django.utils.timezone import now
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django_hosts.resolvers import reverse
from tempfile import TemporaryFile

from folk_rnn_site.models import conform_abc
from composer.models import RNNTune
from composer.forms import ComposeForm, ArchiveForm
from composer.dataset import dataset_as_csv
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
                # For RNN Tunes, the manual input field check_valid_abc is redundant. 
                # It can however serve as "is valid" flag for the tune page metadata display.
                try:
                    conform_abc(tune.abc)
                    is_valid = True
                except:
                    is_valid = False
                tune_in_archive = Tune(rnn_tune=tune, abc=tune.abc, check_valid_abc=is_valid)
                tune_in_archive.title = form.cleaned_data['title']
                tune_in_archive.save()
            return redirect(reverse('tune', host='archiver', kwargs={'tune_id': tune_in_archive.id}))
    return redirect('/')

def dataset_download(request):
    with TemporaryFile(mode='w+') as f:
        dataset_as_csv(f)
        response = HttpResponse(dFile(f), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="folkrnn_dataset_{}"'.format(now().strftime('%Y%m%d-%H%M%S'))
        return response

def competition_page(request):
    return render(request, 'composer/competition.html', {})