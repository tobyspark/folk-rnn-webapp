from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import HttpResponse
from django.core.files import File as dFile
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from tempfile import TemporaryFile
from itertools import chain
from datetime import timedelta

from folk_rnn_site.models import ABCModel, conform_abc
from archiver import MAX_RECENT_ITEMS, TUNE_PREVIEWS_PER_PAGE
from archiver.models import User, Tune, TuneAttribution, Setting, Comment, Recording, Event, TunebookEntry
from archiver.forms import (
                            AttributionForm, 
                            SettingForm, 
                            CommentForm, 
                            ContactForm, 
                            TuneForm, 
                            RecordingForm, 
                            EventForm, 
                            TunebookForm,
                            TuneSearchForm,
                            )
from archiver.dataset import dataset_as_csv

def add_abc_trimmed(tunes):
    for tune in tunes:
        abc_trimmed = ABCModel(abc = tune.abc)
        abc_trimmed.title = None
        abc_trimmed.body = abc_trimmed.body.partition('\n')[0]
        tune.abc_trimmed = abc_trimmed.abc

def activity(filter_dict={}):
    qs_tune = Tune.objects.filter(**filter_dict).order_by('-id')[:MAX_RECENT_ITEMS]
    qs_setting = Setting.objects.filter(**filter_dict).order_by('-id')[:MAX_RECENT_ITEMS]
    # models are not similar enough for...
    # qs_both = qs_tune.union(qs_setting).order_by('submitted')[:MAX_RECENT_ITEMS]
    tunes_settings = list(chain(qs_tune, qs_setting))
    tunes_settings.sort(key=lambda x: x.submitted)
    tunes_settings[:-MAX_RECENT_ITEMS] = []
    
    add_abc_trimmed(tunes_settings)
    
    comments = Comment.objects.filter(**filter_dict).order_by('-id')[:MAX_RECENT_ITEMS]
    
    return (tunes_settings, comments)

def home_page(request):
    tunes_settings, comments = activity()
    return render(request, 'archiver/home.html', {
                            'tunes_settings': tunes_settings,
                            'comments': comments,
                                })

def tunes_page(request):
    if 'search' in request.GET and request.GET['search'] != '':
        search_text = request.GET['search']
        search_results = Tune.objects.annotate(
                search=SearchVector('abc', 'setting__abc', 'tuneattribution__text')
            ).filter(
                search=SearchQuery(search_text)
            ).order_by('-id').distinct('id')
        add_abc_trimmed(search_results)
    else:
        search_results = None
    
    recent_tunes, comments = activity()
    return render(request, 'archiver/tunes.html', {
                            'tunesearch_form': TuneSearchForm(request.GET),
                            'search_results': search_results,
                            'recent_tunes': recent_tunes,
                            'comments': comments,
                            })

def tune_page(request, tune_id=None):
    try:
        tune_id_int = int(tune_id)
        tune = Tune.objects.get(id=tune_id_int)
    except (TypeError, Tune.DoesNotExist):
        return redirect('/')
    
    # Auto-assign logged-in user for just-submitted folk-rnn tune
    default_author = 1
    if (tune.rnn_tune is not None 
            and tune.author_id == default_author
            and request.user.is_authenticated
            and now() - tune.submitted < timedelta(seconds=5)):
        tune.author = request.user
        tune.save()
    
    # Make page
    attribution_form = None
    setting_form = None
    comment_form = None
    if request.user.is_authenticated:
        if tune.author_id in [default_author, request.user.id]:
            attribution = TuneAttribution.objects.filter(tune=tune).first()
            if attribution:
                attribution_form = AttributionForm({
                                                'text': attribution.text,
                                                'url': attribution.url,
                                                })
            else:
                attribution_form = AttributionForm()
        setting_form = SettingForm({
            'abc': conform_abc(tune.abc, raise_if_invalid=False)
        })
        comment_form = CommentForm()
        if request.method == 'POST':
            if 'submit-attribution' in request.POST:
                attribution_form = AttributionForm(request.POST)
                if attribution_form.is_valid():
                    tune.author = request.user
                    tune.save()
                    attribution = TuneAttribution.objects.filter(tune=tune).first()
                    if not attribution:
                        attribution = TuneAttribution(tune=tune)
                    attribution.text = attribution_form.cleaned_data['text']
                    attribution.url = attribution_form.cleaned_data['url']
                    attribution.save()
            elif 'submit-setting' in request.POST:
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
            elif 'submit-comment' in request.POST:
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
            elif 'submit-tunebook-0' in request.POST:
                form = TunebookForm(request.POST)
                if form.is_valid():
                    if form.cleaned_data['add']:
                        TunebookEntry.objects.get_or_create(
                            tune=tune,
                            user=request.user,
                            )
                    else:
                        TunebookEntry.objects.filter(
                            tune=tune,
                            user=request.user,
                            ).delete()
            else:
                # submit-tunebook-x in request.POST where x>0
                setting_x = None
                for k in request.POST:
                    if k[:16] == 'submit-tunebook-':
                        try:
                            setting_x = int(k[16])
                        except:
                            pass
                        break
                if setting_x is None:
                    print('Unknown POST on /tune/x', request.POST)
                else:
                    setting = tune.setting_set.all()[setting_x-1]
                    form = TunebookForm(request.POST)
                    if form.is_valid():
                        if form.cleaned_data['add']:
                            TunebookEntry.objects.get_or_create(
                                setting=setting,
                                user=request.user,
                                )
                        else:
                            TunebookEntry.objects.filter(
                                setting=setting,
                                user=request.user,
                                ).delete()

    
    abc_trimmed = ABCModel(abc = tune.abc)
    abc_trimmed.title = None
    tune.abc_trimmed = abc_trimmed.abc
    tune.tunebook_count = TunebookEntry.objects.filter(tune=tune).count()
    if request.user.is_authenticated:
        tune.other_tunebook_count = TunebookEntry.objects.filter(tune=tune).exclude(user=request.user).count()
        tune.tunebook_form = TunebookForm({'add': TunebookEntry.objects.filter(
                                                    user=request.user, 
                                                    tune=tune,
                                                    ).exists()})
    
    settings = tune.setting_set.all()
    for setting in settings:
        abc_trimmed = ABCModel(abc = setting.abc)
        abc_trimmed.title = None
        setting.abc_trimmed = abc_trimmed.abc
        setting.tunebook_count = TunebookEntry.objects.filter(setting=setting).count()
        if request.user.is_authenticated:
            setting.other_tunebook_count = TunebookEntry.objects.filter(setting=setting).exclude(user=request.user).count()
            setting.tunebook_form = TunebookForm({'add': TunebookEntry.objects.filter(
                                                        user=request.user, 
                                                        setting=setting,
                                                        ).exists()})
        
    return render(request, 'archiver/tune.html', {
        'tune': tune,
        'settings': settings,
        'comments': tune.comment_set.all(),
        'attribution_form': attribution_form,
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

def user_page(request, user_id=None):
    try:
        user_id_int = int(user_id)
        user = User.objects.get(id=user_id_int)
    except (TypeError, User.DoesNotExist):
        return redirect('/')
    
    tunebook_count = TunebookEntry.objects.filter(user=user).count()
    tunebook = TunebookEntry.objects.filter(user=user).order_by('-id')[:MAX_RECENT_ITEMS]
    add_abc_trimmed(tunebook)
    
    tunes_settings, comments = activity({'author': user})
    return render(request, 'archiver/profile.html', {
                            'profile': user,
                            'tunebook_count': tunebook_count,
                            'tunebook': tunebook,
                            'tunes_settings': tunes_settings,
                            'comments': comments,
                            })

def tunebook_page(request, user_id):
    try:
        user_id_int = int(user_id)
        user = User.objects.get(id=user_id_int)
    except (TypeError, User.DoesNotExist):
        return redirect('/')
    
    tunebook = TunebookEntry.objects.filter(user=user).order_by('-id')
    add_abc_trimmed(tunebook)
    
    paginator = Paginator(tunebook, TUNE_PREVIEWS_PER_PAGE)
    page_number = request.GET.get('page')
    try:
        tunebook_page = paginator.page(page_number)
    except PageNotAnInteger:
        tunebook_page = paginator.page(1)
    except EmptyPage:
        tunebook_page = paginator.page(paginator.num_pages)
        
    return render(request, 'archiver/tunebook.html', {
                            'profile': user,
                            'tunebook': tunebook_page,
                            })

def tunebook_download(request, user_id):
    try:
        user_id_int = int(user_id)
        user = User.objects.get(id=user_id_int)
    except (TypeError, User.DoesNotExist):
        return redirect('/')

    tunebook_qs = TunebookEntry.objects.filter(user=user).order_by('id')
    tunebook = [ABCModel(abc=x.abc) for x in tunebook_qs]
    for idx, tune in enumerate(tunebook):
        tune.header_x = idx
    
    tunebook_abc = f'% Tunebook – {user.get_full_name()}\n'
    tunebook_abc += f"% https://themachinefolksession.org{request.path}\n\n\n"
    tunebook_abc += '\n\n'.join([x.abc for x in tunebook])
    
    response = HttpResponse(tunebook_abc, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="themachinefolksession_tunebook_{user_id}'
    return response

def submit_page(request):
    if request.method == 'POST' and 'submit-tune' in request.POST:
            tune_form = TuneForm(request.POST)
            if tune_form.is_valid():
                tune = Tune.objects.create(
                        abc=tune_form.cleaned_data['abc'], 
                        author=request.user,
                        )
                TuneAttribution.objects.create(
                                        tune=tune,
                                        text=tune_form.cleaned_data['text'],
                                        url=tune_form.cleaned_data['url'],
                                        )
                return redirect(reverse('tune', kwargs={"tune_id": tune.id}))
    else:
        tune_form = TuneForm()

    if request.method == 'POST' and 'submit-recording' in request.POST:
            recording_form = RecordingForm(request.POST)
            if recording_form.is_valid():
                recording = Recording.objects.create(
                        title=recording_form.cleaned_data['title'], 
                        body=recording_form.cleaned_data['body'], 
                        date=recording_form.cleaned_data['date'],
                        video = recording_form.cleaned_data['url'],
                        author=request.user,
                        )
                return redirect(reverse('recording', kwargs={"recording_id": recording.id}))
    else:
        recording_form = RecordingForm()
    
    if request.method == 'POST' and 'submit-event' in request.POST:
            event_form = EventForm(request.POST)
            if event_form.is_valid():
                event = Event.objects.create(
                        title=event_form.cleaned_data['title'], 
                        body=event_form.cleaned_data['body'], 
                        date=event_form.cleaned_data['date'], 
                        author=request.user,
                        )
                return redirect(reverse('event', kwargs={"event_id": event.id}))
    else:
        event_form = EventForm()
    
    return render(request, 'archiver/submit.html', {
                            'tune_form': tune_form,
                            'recording_form': recording_form,
                            'event_form': event_form,
    })

def questions_page(request):
    return render(request, 'archiver/questions.html', {
    })

def help_page(request):
    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            message = contact_form.cleaned_data['text']
            if request.user.is_authenticated():
                from_email = request.user.email
                from_user_url = reverse('user', kwargs={'user_id': request.user.id})
                message += f"\n\n--\nAuthenticated user: { request.user.get_full_name() }\n{ from_email }\n{ request.META['HTTP_ORIGIN'] }{ from_user_url }"
            elif 'email' in contact_form.cleaned_data:
                from_email = contact_form.cleaned_data['email']
                message += f'\n\n--\nUnauthenticated user\n{ from_email }'
            else:
                from_email = None
            admin_user = User.objects.first()
            admin_user.email_user(
                        'Message from Contact Form',
                        message,
                        from_email=from_email, # SMTP may ignore from_email, depends on service used.
                        )
            return redirect(request.path)
    else:
        contact_form = ContactForm()
    
    return render(request, 'archiver/help.html', {
                            'contact_form': contact_form,
    })

def dataset_download(request):
    with TemporaryFile(mode='w+') as f:
        dataset_as_csv(f)
        response = HttpResponse(dFile(f), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="folkrnn_dataset_{}"'.format(now().strftime('%Y%m%d-%H%M%S'))
        return response
