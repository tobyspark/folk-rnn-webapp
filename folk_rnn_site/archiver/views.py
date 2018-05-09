from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.core.files import File as dFile
from django.utils.timezone import now
from django.contrib.auth.models import User
from tempfile import TemporaryFile
from itertools import chain

from folk_rnn_site.models import conform_abc
from archiver import MAX_RECENT_ITEMS
from archiver.models import Tune, Setting, Comment
from archiver.forms import SettingForm, CommentForm, SignupForm
from archiver.dataset import dataset_as_csv

def home_page(request):
    return render(request, 'archiver/home.html', {
                                'tunes': Tune.objects.order_by('-id')[:MAX_RECENT_ITEMS],
                                'settings': Setting.objects.order_by('-id')[:MAX_RECENT_ITEMS],
                                'comments': Comment.objects.order_by('-id')[:MAX_RECENT_ITEMS],
                                })

def tunes_page(request):
    qs_tune = Tune.objects.order_by('-id')[:MAX_RECENT_ITEMS]
    qs_setting = Setting.objects.order_by('-id')[:MAX_RECENT_ITEMS]
    # models are not similar enough for...
    # qs_both = qs_tune.union(qs_setting).order_by('submitted')[:MAX_RECENT_ITEMS]
    tunes_settings = list(chain(qs_tune, qs_setting))
    tunes_settings.sort(key=lambda x: x.submitted)
    return render(request, 'archiver/tunes.html', {
                            'tunes_settings': tunes_settings[:MAX_RECENT_ITEMS],
                            'comments': Comment.objects.order_by('-id')[:MAX_RECENT_ITEMS],
                            })

def tune_page(request, tune_id=None):
    try:
        tune_id_int = int(tune_id)
        tune = Tune.objects.get(id=tune_id_int)
    except (TypeError, Tune.DoesNotExist):
        return redirect('/')
    
    setting_form = SettingForm({
        'abc': conform_abc(tune.abc, raise_if_invalid=False)
    })
    comment_form = CommentForm()
    if request.method == 'POST':
        if 'submit_setting' in request.POST:
            form = SettingForm(request.POST)
            if form.is_valid():
                try:
                    print(request.user)
                    Setting.objects.create_setting(
                        tune=tune,
                        abc=form.cleaned_data['abc'],
                        author=request.user,
                        )
                except Exception as e:
                    setting_form = form
                    setting_form.add_error('abc', e) 
            else:
                setting_form = form
        elif 'submit_comment' in request.POST:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = Comment(
                            tune=tune, 
                            text=form.cleaned_data['text'], 
                            author=request.user,
                            )
                comment.save()
            else:
                comment_form = form

    return render(request, 'archiver/tune.html', {
        'tune': tune,
        'settings': Setting.objects.filter(tune=tune),
        'comments': Comment.objects.filter(tune=tune),
        'setting_form': setting_form,
        'comment_form': comment_form,
        })

def dataset_download(request):
    with TemporaryFile(mode='w+') as f:
        dataset_as_csv(f)
        response = HttpResponse(dFile(f), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="folkrnn_dataset_{}"'.format(now().strftime('%Y%m%d-%H%M%S'))
        return response
        
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            password = form.cleaned_data.get('password')
            email = form.cleaned_data.get('email')
            try:
                user = User.objects.create_user(name, email, password)
                login(request, user)
                return redirect('/')
            except Exception as error:
                form.add_error(None, ValidationError(error)) # TODO: parse error into correct field
    else:
        form = SignupForm()
    
    return render(request, 'registration/signup.html', {
        'form': form,
    })