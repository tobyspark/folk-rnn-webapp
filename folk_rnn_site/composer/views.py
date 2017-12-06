from django.shortcuts import redirect, render

from composer.models import CandidateTune, ArchiveTune, Comment
from composer.forms import ComposeForm, CandidateForm, CommentForm

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
    if request.method == 'POST':
        form = CandidateForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['edit_state'] == 'user':
                tune.user_tune = form.cleaned_data['tune']
                tune.save()
            if form.cleaned_data['edit'] == 'rnn':
                show_user = False
            if 'archive' in request.POST:
                tune_abc = tune.tune()
                # TODO: Check there isn't already an archived tune with this abc from this candidate
                # TODO: Check it has a new title
                archive_tune = ArchiveTune(candidate=tune, tune=tune_abc)
                archive_tune.save()
                return redirect('/tune/{}'.format(archive_tune.id))
                
    if show_user:
        form = CandidateForm({
                    'tune': tune.tune(),
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