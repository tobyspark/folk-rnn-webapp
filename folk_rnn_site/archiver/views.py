from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.core.files import File as dFile
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from tempfile import TemporaryFile
from itertools import chain

from folk_rnn_site.models import ABCModel, conform_abc
from archiver import MAX_RECENT_ITEMS
from archiver.models import User, Tune, TuneAttribution, Setting, Comment, Recording, Event
from archiver.forms import SettingForm, CommentForm, SignupForm
from archiver.dataset import dataset_as_csv

def activity():
    qs_tune = Tune.objects.order_by('-id')[:MAX_RECENT_ITEMS]
    qs_setting = Setting.objects.order_by('-id')[:MAX_RECENT_ITEMS]
    # models are not similar enough for...
    # qs_both = qs_tune.union(qs_setting).order_by('submitted')[:MAX_RECENT_ITEMS]
    tunes_settings = list(chain(qs_tune, qs_setting))
    tunes_settings.sort(key=lambda x: x.submitted)
    tunes_settings[MAX_RECENT_ITEMS:] = []
    
    for tune in tunes_settings:
        abc_trimmed = ABCModel(abc = tune.abc)
        abc_trimmed.title = None
        abc_trimmed.body = abc_trimmed.body.partition('\n')[0]
        tune.abc_trimmed = abc_trimmed.abc
    
    comments = Comment.objects.order_by('-id')[:MAX_RECENT_ITEMS]
    
    return (tunes_settings, comments)

def home_page(request):
    tunes_settings, comments = activity()
    return render(request, 'archiver/home.html', {
                            'tunes_settings': tunes_settings,
                            'comments': comments,
                                })

def tunes_page(request):
    tunes_settings, comments = activity()
    return render(request, 'archiver/tunes.html', {
                            'tunes_settings': tunes_settings,
                            'comments': comments,
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
    
    abc_trimmed = ABCModel(abc = tune.abc)
    abc_trimmed.title = None
    tune.abc_trimmed = abc_trimmed.abc
    
    settings = tune.setting_set.all()
    for setting in settings:
        abc_trimmed = ABCModel(abc = setting.abc)
        abc_trimmed.title = None
        setting.abc_trimmed = abc_trimmed.abc
        
    return render(request, 'archiver/tune.html', {
        'tune': tune,
        'settings': settings,
        'comments': tune.comment_set.all(),
        'setting_form': setting_form,
        'comment_form': comment_form,
        })

def tune_download(request, tune_id=None):
    try:
        tune_id_int = int(tune_id)
        tune = Tune.objects.get(id=tune_id_int)
    except (TypeError, Tune.DoesNotExist):
        return redirect('/')

    response = HttpResponse(tune.abc, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="themachinefolksession_tune_{tune_id}"'
    return response

def setting_download(request, tune_id=None, setting_id=None):
    try:
        tune_id_int = int(tune_id)
        tune = Tune.objects.get(id=tune_id_int)
    except (TypeError, Tune.DoesNotExist):
        return redirect('/')

    try:
        settings = tune.setting_set.all()
        abc = [x.abc for x in settings if x.header_x == setting_id][0]
    except (IndexError):
        return redirect('/')
    
    response = HttpResponse(abc, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="themachinefolksession_tune_{tune_id}_setting_{setting_id}"'
    return response

def tune_setting_download(request, tune_id=None):
    try:
        tune_id_int = int(tune_id)
        tune = Tune.objects.get(id=tune_id_int)
    except (TypeError, Tune.DoesNotExist):
        return redirect('/')
    
    tune_zeroed = ABCModel(abc=tune.abc)
    tune_zeroed.header_x = 0
    settings = tune.setting_set.all()
    abc_tunebook = '\n\n'.join([tune_zeroed.abc] + [x.abc for x in settings])

    response = HttpResponse(abc_tunebook, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="themachinefolksession_tune_{tune_id}_and_settings"'
    return response

def recordings_page(request):
    return render(request, 'archiver/recordings.html', {
        'recordings': Recording.objects.all()
    })

def recording_page(request, recording_id=None):
    try:
        recording_id_int = int(recording_id)
        recording = Recording.objects.get(id=recording_id_int)
    except (TypeError, Recording.DoesNotExist):
        return redirect('/')

    return render(request, 'archiver/recordings.html', {
        'recordings': [recording],
    })

def events_page(request):
    return render(request, 'archiver/events.html', {
        'events': Event.objects.all()
    })

def event_page(request, event_id=None):
    try:
        event_id_int = int(event_id)
        event = Event.objects.get(id=event_id_int)
    except (TypeError, Event.DoesNotExist):
        return redirect('/')
    
    return render(request, 'archiver/events.html', {
        'events': [event],
    })

def submit_page(request):
    return render(request, 'archiver/submit.html', {
    })

def questions_page(request):
    return render(request, 'archiver/questions.html', {
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
        form.add_error('password', "...we're working on opening up the community features. Sign-up is currently disabled.")
        # FIXME: Re-enable for site launch with community features
        # if form.is_valid():
        #     first_name = form.cleaned_data.get('first_name')
        #     last_name = form.cleaned_data.get('last_name')
        #     password = form.cleaned_data.get('password')
        #     email = form.cleaned_data.get('email')
        #     try:
        #         user = User.objects.create_user(email, password, first_name=first_name, last_name=last_name)
        #         login(request, user)
        #         return redirect('/')
        #     except Exception as error:
        #         form.add_error(None, ValidationError(error)) # TODO: parse error into correct field
    else:
        form = SignupForm()
    
    return render(request, 'registration/signup.html', {
        'form': form,
    })