from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.core.files import File as dFile
from django.utils.timezone import now
from tempfile import TemporaryFile

from composer.models import CandidateTune, ArchiveTune, Comment
from composer.forms import ComposeForm, CandidateForm, CommentForm
from composer.dataset import dataset_as_csv

MAX_RECENT_ITEMS = 5

def home_page(request):
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
    
    return render(request, 'home.html', {
                                'form': form,
                                'tunes': ArchiveTune.objects.order_by('-id')[:MAX_RECENT_ITEMS],
                                'comments': Comment.objects.order_by('-id')[:MAX_RECENT_ITEMS],
                                })

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
            'candidate_id': tune_id_int,
            })
    
    if not tune.rnn_finished:
        return render(request, 'candidate-tune-in-process.html', {
            'prime_tokens': tune.prime_tokens,
            'rnn_has_started': True,
            'candidate_id': tune_id_int,
            })
    
    show_user = True
    archive = False
    if request.method == 'POST':
        form = CandidateForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['edit_state'] == 'user':
                tune.user_tune = form.cleaned_data['tune']
                tune.save()
            if form.cleaned_data['edit'] == 'rnn':
                show_user = False
            if 'archive' in request.POST:
                archive = True
                                
    if show_user:
        form = CandidateForm({
                    'tune': tune.tune,
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
    
    if archive:
        # Check there isn't already an archived tune with this abc body
        for archive_tune in ArchiveTune.objects.all():
            if archive_tune.body == tune.body:
                archive = False
                if show_user:
                    form.add_error('tune', 'This development is already archived as {}. You can still develop it further and archive that.'.format(archive_tune.title))
                else:
                    form.add_error('tune', 'This RNN original is already archived as {}. You can still develop it and archive your version.'.format(archive_tune.title))
                break
        
        # Check it has a new, unique title
        if tune.title.startswith('Folk RNN Candidate Tune'):
            archive = False
            form.add_error('tune', 'Provide your own title (edit the abc "T: ..." line)')
        if any(x.title == tune.title for x in ArchiveTune.objects.all()):
            archive = False
            form.add_error('tune', 'Already an archived tune with this title.')
        
        if archive:
            archive_tune = ArchiveTune(candidate=tune, tune=tune.tune)
            archive_tune.save()
            return redirect('/tune/{}'.format(archive_tune.id))

    return render(request, 'candidate-tune.html', {
        'candidate_id': tune_id_int,
        'model': tune.rnn_model_name,
        'seed': tune.seed,
        'temp': tune.temp,
        'prime_tokens': tune.prime_tokens,
        'requested': tune.requested,
        'rnn_duration': (tune.rnn_finished - tune.rnn_started).total_seconds(),
        'form': form,
        'show_user': show_user,
        })

def archive_tune_page(request, tune_id=None):
    try:
        tune_id_int = int(tune_id)
        tune = ArchiveTune.objects.get(id=tune_id_int)
    except (TypeError, ArchiveTune.DoesNotExist):
        return redirect('/')
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = Comment(
                        tune=tune, 
                        text=form.cleaned_data['text'], 
                        author=form.cleaned_data['author'],
                        )
            comment.save()
    else:
        form = CommentForm()
    
    tune_lines = tune.tune.split('\n')

    return render(request, 'archive-tune.html', {
        'tune': tune,
        'tune_cols': max(len(line) for line in tune_lines), # TODO: look into autosize via CSS, when CSS is a thing round here.
        'tune_rows': len(tune_lines),
        'form': form,
        'comments': Comment.objects.filter(tune=tune),
        })
        
def dataset_download(request):
    with TemporaryFile(mode='w+') as f:
        dataset_as_csv(f)
        response = HttpResponse(dFile(f), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="folkrnn_dataset_{}"'.format(now().strftime('%Y%m%d-%H%M%S'))
        return response