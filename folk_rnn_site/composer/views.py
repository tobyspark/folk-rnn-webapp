from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.core.files import File as dFile
from django.utils.timezone import now
from channels import Channel
from tempfile import TemporaryFile

from composer.models import Tune, Setting, Comment
from composer.forms import ComposeForm, TuneForm, CommentForm
from composer.dataset import dataset_as_csv

MAX_RECENT_ITEMS = 5

def home_page(request):
    if request.method == 'POST':
        form = ComposeForm(request.POST)
        if form.is_valid():
            tune = Tune()
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
            Channel('folk_rnn').send({'message': 'hello world, via channels'})
            return redirect('/tune/{}'.format(tune.id))
    else:
        form = ComposeForm()
    
    return render(request, 'home.html', {
                                'form': form,
                                'tunes': Tune.objects.order_by('-id')[:MAX_RECENT_ITEMS],
                                'settings': Setting.objects.order_by('-id')[:MAX_RECENT_ITEMS],
                                'comments': Comment.objects.order_by('-id')[:MAX_RECENT_ITEMS],
                                })

def tune_page(request, tune_id=None):
    try:
        tune_id_int = int(tune_id)
        tune = Tune.objects.get(id=tune_id_int)
    except (TypeError, Tune.DoesNotExist):
        return redirect('/')
    
    # Handle rnn-in-process
    
    if not tune.rnn_started:
        return render(request, 'tune-in-process.html', {
            'prime_tokens': tune.prime_tokens,
            'rnn_has_started': False,
            'candidate_id': tune_id_int,
            })
    
    if not tune.rnn_finished:
        return render(request, 'tune-in-process.html', {
            'prime_tokens': tune.prime_tokens,
            'rnn_has_started': True,
            'candidate_id': tune_id_int,
            })
    
    # Default content
    tune_form = TuneForm({
                    'tune': tune.abc,
                    'edit': 'user',
                    'edit_state': 'user',
                    })
    comment_form = CommentForm()
    
    # Handle POST
    if request.method == 'POST':
        if 'tune' in request.POST:
            form = TuneForm(request.POST)
            if form.is_valid():
                if form.cleaned_data['edit_state'] == 'user':
                    try:
                        tune.abc = form.cleaned_data['tune']
                        tune.save()
                        tune_form = TuneForm({
                                        'tune': tune.abc, # now conformed
                                        'edit': 'user',
                                        'edit_state': 'user',
                                        })
                    except AttributeError as e:
                        tune_form = form
                        tune_form.add_error('tune', e) 
                if form.cleaned_data['edit'] == 'rnn':
                    tune_form = TuneForm({
                                    'tune': tune.abc_rnn,
                                    'edit': 'rnn',
                                    'edit_state': 'rnn',
                                    })
                    tune_form.fields['tune'].widget.attrs['readonly'] = True
                if 'submit_setting' in request.POST:
                    try:
                        Setting.objects.create_setting(tune)
                    except ValueError as e:
                        tune_form = form
                        tune_form.add_error('tune', e)
        elif 'submit_comment' in request.POST:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = Comment(
                            tune=tune, 
                            text=form.cleaned_data['text'], 
                            author=form.cleaned_data['author'],
                            )
                comment.save()
            else:
                comment_form = form
        
    tune_lines = tune.abc.split('\n')
    
    return render(request, 'tune.html', {
        'tune': tune,
        'settings': Setting.objects.filter(tune=tune),
        'comments': Comment.objects.filter(tune=tune),
        'tune_form': tune_form,
        'comment_form': comment_form,
        'rnn_duration': (tune.rnn_finished - tune.rnn_started).total_seconds(),
        'tune_cols': max(len(line) for line in tune_lines), # TODO: look into autosize via CSS, when CSS is a thing round here.
        'tune_rows': len(tune_lines),
        })
        
def dataset_download(request):
    with TemporaryFile(mode='w+') as f:
        dataset_as_csv(f)
        response = HttpResponse(dFile(f), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="folkrnn_dataset_{}"'.format(now().strftime('%Y%m%d-%H%M%S'))
        return response