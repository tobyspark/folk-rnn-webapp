from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import HttpResponse
from django.core.files import File as dFile
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Q, Count
from tempfile import TemporaryFile
from itertools import chain
from datetime import timedelta
from random import choice, choices

from folk_rnn_site.models import ABCModel
from archiver import TUNE_SEARCH_EXAMPLES, MAX_RECENT_ITEMS, TUNE_PREVIEWS_PER_PAGE
from archiver import weightedSelectionWithoutReplacement
from archiver.models import User, Tune, TuneAttribution, Setting, Comment, Recording, Event, TunebookEntry, TuneRecording
from archiver.forms import (
                            AttributionForm, 
                            SettingForm, 
                            CommentForm, 
                            ContactForm, 
                            TuneForm,
                            TuneAttributionForm, 
                            RecordingForm, 
                            EventForm, 
                            TunebookForm,
                            SearchForm,
                            )
from archiver.dataset import dataset_as_csv

def add_counts(tunes):
    # see also interesting_tunes queryset annotation
    for result in tunes:
        result.setting__count = result.setting_set.count()
        result.comment__count = result.comment_set.count() 
        result.recording__count = result.tunerecording_set.count() 
        result.event__count = result.tuneevent_set.count()
        result.tunebook__count = result.tunebookentry_set.count()

def activity(filter_dict={}):
    qs_tune = Tune.objects.filter(**filter_dict).order_by('-id')[:MAX_RECENT_ITEMS]
    qs_setting = Setting.objects.filter(**filter_dict).order_by('-id')[:MAX_RECENT_ITEMS]
    # models are not similar enough for...
    # qs_both = qs_tune.union(qs_setting).order_by('submitted')[:MAX_RECENT_ITEMS]
    tunes_settings = list(chain(qs_tune, qs_setting))
    tunes_settings.sort(key=lambda x: x.submitted)
    tunes_settings[:-MAX_RECENT_ITEMS] = []
    
    comments = Comment.objects.filter(**filter_dict).order_by('-id')[:MAX_RECENT_ITEMS]
    
    return (tunes_settings, comments)

def home_page(request):
    q = Q(setting__count__gt=0) | Q(comment__count__gt=0) | Q(recording__count__gt=0) | Q(event__count__gt=0) | Q(tunebook__count__gt=0)
    interesting_tunes = Tune.objects.annotate(
        Count('setting', distinct=True), 
        Count('comment', distinct=True), 
        recording__count=Count('tunerecording', distinct=True), 
        event__count=Count('tuneevent', distinct=True),
        tunebook__count=Count('tunebookentry', distinct=True),
    ).filter(q)
    tune_saliency = [x.tunebook__count*3 + x.setting__count*3 + x.recording__count*2 + x.event__count*2 + x.comment__count for x in interesting_tunes]
    
    if len(interesting_tunes) > MAX_RECENT_ITEMS:
        tune_selection = weightedSelectionWithoutReplacement(interesting_tunes, tune_saliency, k=MAX_RECENT_ITEMS)
    else:
        tune_selection = Tune.objects.all()[-MAX_RECENT_ITEMS:]
    
    recording = None
    for tune in tune_selection:
        candidate_recordings = TuneRecording.objects.filter(tune=tune)
        if len(candidate_recordings):
            recording = choice(candidate_recordings).recording
            break
    if recording is None:
        try:
            recording = choice(Recording.objects.all())
        except:
            recording = None
    
    return render(request, 'archiver/home.html', {
                            'recording': recording,
                            'tunes': tune_selection,
                            })

def tunes_page(request):
    if 'search' in request.GET and request.GET['search'] != '':
        search_text = request.GET['search']
        search_results = Tune.objects.annotate(
                search=SearchVector('abc', 'setting__abc', 'tuneattribution__text', 'comment__text')
            ).filter(
                search=SearchQuery(search_text)
            ).order_by('-id').distinct('id')
    else:
        search_text = ''
        search_results = Tune.objects.order_by('-id')
        
    paginator = Paginator(search_results, TUNE_PREVIEWS_PER_PAGE)
    page_number = request.GET.get('page')
    try:
        search_results_page = paginator.page(page_number)
    except PageNotAnInteger:
        search_results_page = paginator.page(1)
    except EmptyPage:
        search_results_page = paginator.page(paginator.num_pages)
    add_counts(search_results_page)
    
    return render(request, 'archiver/tunes.html', {
                            'search_form': SearchForm(request.GET),
                            'search_text': search_text,
                            'search_examples': TUNE_SEARCH_EXAMPLES,
                            'search_results': search_results_page,
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
            'abc': tune.abc,
            'check_valid_abc': True,
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
                setting = Setting(
                            tune=tune,
                            author=request.user,
                            )
                form = SettingForm(request.POST, instance=setting)
                if form.is_valid():
                    form.save() 
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

    tune.tunebook_count = TunebookEntry.objects.filter(tune=tune).count()
    if request.user.is_authenticated:
        tune.other_tunebook_count = TunebookEntry.objects.filter(tune=tune).exclude(user=request.user).count()
        tune.tunebook_form = TunebookForm({'add': TunebookEntry.objects.filter(
                                                    user=request.user, 
                                                    tune=tune,
                                                    ).exists()})
    
    settings = tune.setting_set.all()
    for setting in settings:
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

    response = HttpResponse(tune.abc_with_attribution, content_type='text/plain')
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
        abc = [x.abc_with_attribution for x in settings if x.header_x == setting_id][0]
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
    
    tune_zeroed = ABCModel(abc=tune.abc_with_attribution)
    tune_zeroed.header_x = 0
    settings = tune.setting_set.all()
    abc_tunebook = '\n\n'.join([tune_zeroed.abc] + [x.abc_with_attribution for x in settings])

    response = HttpResponse(abc_tunebook, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="themachinefolksession_tune_{tune_id}_and_settings"'
    return response

def recordings_page(request):
    if 'search' in request.GET and request.GET['search'] != '':
        search_text = request.GET['search']
        search_results = Recording.objects.annotate(
                search=SearchVector('title', 'body', 'event__title', 'tunerecording__tune__abc')
            ).filter(
                search=SearchQuery(search_text)
            ).order_by('-id').distinct('id')
    else:
        search_text = ''
        search_results = Recording.objects.order_by('-id')
    
    paginator = Paginator(search_results, TUNE_PREVIEWS_PER_PAGE)
    page_number = request.GET.get('page')
    try:
        search_results_page = paginator.page(page_number)
    except PageNotAnInteger:
        search_results_page = paginator.page(1)
    except EmptyPage:
        search_results_page = paginator.page(paginator.num_pages)
    
    search_placeholders = ['Ensemble x.y', 'Partnerships', 'St. Dunstan']
    search_placeholder = f'e.g. {choice(search_placeholders)}'
    return render(request, 'archiver/recordings.html', {
        'search_form': SearchForm(request.GET),
        'search_text': search_text,
        'search_placeholder': search_placeholder,
        'search_results': search_results_page,
    })

def recording_page(request, recording_id=None):
    try:
        recording_id_int = int(recording_id)
        recording = Recording.objects.get(id=recording_id_int)
    except (TypeError, Recording.DoesNotExist):
        return redirect('/')

    return render(request, 'archiver/recording.html', {
        'recording': recording,
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
    tunebook = [ABCModel(abc=x.abc_with_attribution) for x in tunebook_qs]
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
            tune = Tune(author=request.user)
            tune_form = TuneForm(request.POST, instance=tune)
            tune_attribution_form = TuneAttributionForm(request.POST)
            if tune_form.is_valid() and tune_attribution_form.is_valid():
                tune_form.save()
                tune_attribution = TuneAttribution(tune=tune) # tune now has pk
                tune_attribution_form = TuneAttributionForm(request.POST, instance=tune_attribution) 
                tune_attribution_form.save()
                return redirect(reverse('tune', kwargs={"tune_id": tune.id}))
    else:
        tune_form = TuneForm()
        tune_attribution_form = TuneAttributionForm()

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
                            'tune_attribution_form': tune_attribution_form,
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
