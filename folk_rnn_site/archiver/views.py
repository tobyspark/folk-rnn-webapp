from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.core.files import File as dFile
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Q
from actstream import action
from tempfile import TemporaryFile
from itertools import chain
from datetime import timedelta
from random import choice, choices

from folk_rnn_site.models import ABCModel
from archiver import (
                            TUNE_SEARCH_EXAMPLES, 
                            RECORDING_SEARCH_EXAMPLES,
                            COMPETITION_SEARCH_EXAMPLES,
                            MAX_RECENT_ITEMS, 
                            TUNE_PREVIEWS_PER_PAGE,
                            weightedSelectionWithoutReplacement,
                            )
from archiver.models import (
                            User, 
                            Tune, 
                            annotate_counts, 
                            TuneAttribution, 
                            Setting, 
                            TuneComment, 
                            Recording, 
                            Event, 
                            Collection,
                            CollectionEntry, 
                            TuneRecording, 
                            Competition,
                            CompetitionTune,
                            CompetitionTuneVote,
                            CompetitionRecording,
                            CompetitionRecordingVote,
                            CompetitionComment,
                            )
from archiver.forms import (
                            SettingForm, 
                            CommentForm, 
                            ContactForm, 
                            TuneForm,
                            TuneAttributionForm, 
                            RecordingForm, 
                            EventForm, 
                            TunebookForm,
                            SearchForm,
                            VoteForm,
                            )
from archiver.dataset import dataset_as_csv

def activity(filter_dict={}):
    qs_tune = Tune.objects.filter(**filter_dict).order_by('-id')[:MAX_RECENT_ITEMS]
    qs_setting = Setting.objects.filter(**filter_dict).order_by('-id')[:MAX_RECENT_ITEMS]
    # models are not similar enough for...
    # qs_both = qs_tune.union(qs_setting).order_by('submitted')[:MAX_RECENT_ITEMS]
    tunes_settings = list(chain(qs_tune, qs_setting))
    tunes_settings.sort(key=lambda x: x.submitted)
    tunes_settings[:-MAX_RECENT_ITEMS] = []
    
    comments = TuneComment.objects.filter(**filter_dict).order_by('-id')[:MAX_RECENT_ITEMS]
    
    return (tunes_settings, comments)

def home_page(request):
    q = Q(setting__count__gt=0) | Q(comment__count__gt=0) | Q(recording__count__gt=0) | Q(event__count__gt=0) | Q(collection__count__gt=0)
    interesting_tunes = Tune.objects.all().annotate_counts().filter(q).annotate_saliency()
    
    if len(interesting_tunes) > MAX_RECENT_ITEMS:
        tune_selection = weightedSelectionWithoutReplacement(
                                interesting_tunes, 
                                [x.saliency for x in interesting_tunes], 
                                k=MAX_RECENT_ITEMS
                                )
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
        search_results = (
                Tune.objects
                .annotate(search=SearchVector(
                            'abc', 
                            'setting__abc', 
                            'tuneattribution__text',  
                            'author__first_name', 
                            'author__last_name',
                            'comment__text',
                            'comment__author__first_name',
                            'comment__author__last_name',
                            ))
                .filter(search=SearchQuery(search_text))
                )
    else:
        search_text = ''
        search_results = Tune.objects.all()
    
    if 'order_by' in request.GET and request.GET['order_by'] == 'popularity':
        search_results = search_results.annotate_counts().annotate_saliency().order_by('-saliency', '-id')
        order_by = 'popularity'
    else:
        search_results = search_results.order_by('-id').distinct('id')
        order_by = 'added'
        
    page_number = request.GET.get('page')
    items_per_page = TUNE_PREVIEWS_PER_PAGE
    if page_number == 'all' and request.user.is_authenticated:
        items_per_page = 9999
    paginator = Paginator(search_results, items_per_page)
    try:
        search_results_page = paginator.page(page_number)
    except PageNotAnInteger:
        search_results_page = paginator.page(1)
    except EmptyPage:
        search_results_page = paginator.page(paginator.num_pages)
    annotate_counts(search_results_page)
    
    return render(request, 'archiver/tunes.html', {
                            'search_form': SearchForm(request.GET),
                            'search_text': search_text,
                            'order_by': order_by,
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
        action.send(request.user, verb='submitted', action_object=tune)
    
    # Make page
    attribution_form = None
    setting_form = None
    comment_form = None
    if request.user.is_authenticated:
        if tune.author_id in [default_author, request.user.id]:
            attribution = TuneAttribution.objects.filter(tune=tune).first()
            if attribution:
                attribution_form = TuneAttributionForm({
                                                'text': attribution.text,
                                                'url': attribution.url,
                                                })
            else:
                attribution_form = TuneAttributionForm()
        setting_form = SettingForm({
            'abc': tune.abc,
            'check_valid_abc': True,
        })
        comment_form = CommentForm()
        if request.method == 'POST':
            if 'submit-attribution' in request.POST:
                attribution_form = TuneAttributionForm(request.POST)
                if attribution_form.is_valid():
                    if tune.author != request.user:
                        tune.author = request.user
                        tune.save()
                        action.send(request.user, verb='claimed', action_object=tune)
                    attribution = TuneAttribution.objects.filter(tune=tune).first()
                    if not attribution:
                        attribution = TuneAttribution(tune=tune)
                    user_data = attribution_form.cleaned_data['text'], attribution_form.cleaned_data['url']
                    if user_data != (attribution.text, attribution.url):
                        attribution.text, attribution.url = user_data
                        attribution.save()
                        action.send(request.user, verb='updated', action_object=tune)
            elif 'submit-setting' in request.POST:
                setting = Setting(
                            tune=tune,
                            author=request.user,
                            )
                form = SettingForm(request.POST, instance=setting)
                if form.is_valid():
                    form.save() 
                    action.send(request.user, verb='submitted', action_object=setting)
                else:
                    setting_form = form
            elif 'submit-comment' in request.POST:
                form = CommentForm(request.POST)
                if form.is_valid():
                    comment = TuneComment(
                                tune=tune, 
                                text=form.cleaned_data['text'], 
                                author=request.user,
                                )
                    comment.save()
                    action.send(request.user, verb='made', action_object=comment, target=tune)
                else:
                    comment_form = form
            elif 'submit-tunebook-0' in request.POST:
                form = TunebookForm(request.POST)
                if form.is_valid():
                    if form.cleaned_data['add']:
                        CollectionEntry.objects.get_or_create(
                            tune=tune,
                            collection=request.user.tunebook,
                            )
                        action.send(request.user, verb='added', action_object=tune, target=request.user.tunebook)
                    else:
                        CollectionEntry.objects.filter(
                            tune=tune,
                            collection=request.user.tunebook,
                            ).delete()
                        action.send(request.user, verb='removed', action_object=tune, target=request.user.tunebook)
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
                            CollectionEntry.objects.get_or_create(
                                setting=setting,
                                collection=request.user.tunebook,
                                )
                            action.send(request.user, verb='added', action_object=setting, target=request.user.tunebook)
                        else:
                            CollectionEntry.objects.filter(
                                setting=setting,
                                collection=request.user.tunebook,
                                ).delete()
                            action.send(request.user, verb='removed', action_object=setting, target=request.user.tunebook)

    tune.tunebook_count = CollectionEntry.objects.filter(tune=tune).count() #FIXME: collection.user is not null, do when there are non-tunebook collections
    if request.user.is_authenticated:
        tune.other_tunebook_count = (
                            CollectionEntry.objects
                            .filter(tune=tune)
                            .exclude(collection=request.user.tunebook)
                            .count()
                            )
        tune.tunebook_form = TunebookForm({'add': (
                                            CollectionEntry.objects
                                            .filter(tune=tune, collection=request.user.tunebook)
                                            .exists()
                                            )})
    
    settings = tune.setting_set.all()
    for setting in settings:
        setting.tunebook_count = CollectionEntry.objects.filter(setting=setting).count()
        if request.user.is_authenticated:
            setting.other_tunebook_count = (
                                            CollectionEntry.objects
                                            .filter(setting=setting)
                                            .exclude(collection=request.user.tunebook)
                                            .count()
                                            )
            setting.tunebook_form = TunebookForm({'add': (
                                            CollectionEntry.objects
                                            .filter(setting=setting, collection=request.user.tunebook)
                                            .exists()
                                            )})
        
    return render(request, 'archiver/tune.html', {
        'tune': tune,
        'settings': settings,
        'comments': tune.comment_set.all(),
        'attribution_form': attribution_form,
        'setting_form': setting_form,
        'comment_form': comment_form,
        })

def setting_redirect(request, tune_id=None, setting_id=None):
    """
    Redirect /tune/x/setting/y to /tune/x#setting-y
    Note setting_id here is not db id but the setting index, i.e. incremented x within each tune
    """
    try:
        tune_id_int = int(tune_id)
        tune = Tune.objects.get(id=tune_id_int)
    except (TypeError, Tune.DoesNotExist):
        return redirect('/')
    
    if setting_id not in [x.header_x for x in tune.setting_set.all()]:
        return redirect('/')
    
    return redirect(tune.get_absolute_url() + f'#setting-{ setting_id }')

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
        search_results = (
                Recording.objects
                .annotate(search=SearchVector(
                                'title', 
                                'body', 
                                'event__title', 
                                'tunerecording__tune__abc',
                                'author__first_name',
                                'author__last_name',
                                ))
                .filter(search=SearchQuery(search_text))
                .order_by('-id')
                .distinct('id')
                )
    else:
        search_text = ''
        search_results = Recording.objects.order_by('-id')
    
    page_number = request.GET.get('page')
    items_per_page = TUNE_PREVIEWS_PER_PAGE
    if page_number == 'all' and request.user.is_authenticated:
        items_per_page = 9999
    paginator = Paginator(search_results, items_per_page)
    try:
        search_results_page = paginator.page(page_number)
    except PageNotAnInteger:
        search_results_page = paginator.page(1)
    except EmptyPage:
        search_results_page = paginator.page(paginator.num_pages)
    
    search_placeholders = RECORDING_SEARCH_EXAMPLES
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
    tunebook_count = CollectionEntry.objects.filter(collection=user.tunebook).count()
    tunebook_entries = CollectionEntry.objects.filter(collection=user.tunebook).order_by('?')[:1]
    
    for item in tunebook_entries:
        if item.tune:
            item.tunebook_count = CollectionEntry.objects.filter(tune=item.tune).count()
        else:
            item.tunebook_count = CollectionEntry.objects.filter(setting=item.setting).count()
    
    return render(request, 'archiver/profile.html', {
                            'profile': user,
                            'tunebook_count': tunebook_count,
                            'tunebook_entries': tunebook_entries,
                            'activity': user.actor_actions.all()[:TUNE_PREVIEWS_PER_PAGE]
                            })

def tunebook_page(request, user_id):
    try:
        user_id_int = int(user_id)
        user = User.objects.get(id=user_id_int)
    except (TypeError, User.DoesNotExist):
        return redirect('/')
    
    tunebook_entries = CollectionEntry.objects.filter(collection=user.tunebook).order_by('-id')
    
    page_number = request.GET.get('page')
    items_per_page = TUNE_PREVIEWS_PER_PAGE
    if page_number == 'all' and request.user.is_authenticated:
        items_per_page = 9999
    paginator = Paginator(tunebook_entries, items_per_page)
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
    
    tunebook_qs = CollectionEntry.objects.filter(collection=user.tunebook).order_by('id')
    tunebook_entries = [ABCModel(abc=x.abc_with_attribution) for x in tunebook_qs]
    for idx, tune in enumerate(tunebook_entries):
        tune.header_x = idx
    
    tunebook_abc = f'% Tunebook – {user.get_full_name()}\n'
    tunebook_abc += f"% https://themachinefolksession.org{request.path}\n\n\n"
    tunebook_abc += '\n\n'.join([x.abc for x in tunebook_entries])
    
    response = HttpResponse(tunebook_abc, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="themachinefolksession_tunebook_{user_id}'
    return response

def competitions_page(request):
    if 'search' in request.GET and request.GET['search'] != '':
        search_text = request.GET['search']
        search_results = (
                Competition.objects
                .annotate(search=SearchVector(
                        'title', 
                        'text', 
                        'competitiontune__tune__abc',
                        'competitiontune__tune__author__first_name',
                        'competitiontune__tune__author__last_name', 
                        'competitionrecording__recording__title', 
                        'competitionrecording__recording__body', 
                        'competitionrecording__recording__author__first_name', 
                        'competitionrecording__recording__author__last_name',
                        'comment__text',
                        'comment__author__first_name',
                        'comment__author__last_name',
                        ))
                .filter(search=SearchQuery(search_text))
                .order_by('-id')
                .distinct('id')
                )
    else:
        search_text = ''
        search_results = Competition.objects.order_by('-id')
    
    page_number = request.GET.get('page')
    items_per_page = TUNE_PREVIEWS_PER_PAGE
    if page_number == 'all' and request.user.is_authenticated:
        items_per_page = 9999
    paginator = Paginator(search_results, items_per_page)
    try:
        search_results_page = paginator.page(page_number)
    except PageNotAnInteger:
        search_results_page = paginator.page(1)
    except EmptyPage:
        search_results_page = paginator.page(paginator.num_pages)
    
    search_placeholders = COMPETITION_SEARCH_EXAMPLES
    search_placeholder = f'e.g. {choice(search_placeholders)}'
    return render(request, 'archiver/competitions.html', {
        'search_form': SearchForm(request.GET),
        'search_text': search_text,
        'search_placeholder': search_placeholder,
        'search_results': search_results_page,
    })

def competition_page(request, competition_id):
    try:
        competition_id_int = int(competition_id)
        competition = Competition.objects.get(id=competition_id_int)
    except (TypeError, Competition.DoesNotExist):
        return redirect('/')
    
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
            TuneRecording.objects.create(
                    tune=competition.tune_won,
                    recording=recording,
                    )
            CompetitionRecording.objects.create(
                    competition=competition,
                    recording=recording,
                    )
            action.send(request.user, verb='submitted', action_object=recording, target=competition)
            return redirect(competition.get_absolute_url())
    else:
        recording_form = RecordingForm()
    
    if request.method == 'POST' and 'submit-tune-vote' in request.POST:
        tune_vote_form = VoteForm(request.POST)
        if tune_vote_form.is_valid():
            tune_id = tune_vote_form.cleaned_data['object_id']
            competition_tune = CompetitionTune.objects.get(tune__id=tune_id, competition=competition)
            try:
                vote = CompetitionTuneVote.objects.get(votable=competition_tune, user=request.user)
                vote.delete()
                action.send(request.user, verb='retracted their tune vote', action_object=competition)
            except CompetitionTuneVote.DoesNotExist:
                vote = CompetitionTuneVote.objects.create(votable=competition_tune, user=request.user)
                action.send(request.user, verb='cast', action_object=vote)
            return redirect(competition.get_absolute_url())
    
    if request.method == 'POST' and 'submit-recording-vote' in request.POST:
        recording_vote_form = VoteForm(request.POST)
        if recording_vote_form.is_valid():
            recording_id = recording_vote_form.cleaned_data['object_id']
            competition_recording = CompetitionRecording.objects.get(recording__id=recording_id, competition=competition)
            try:
                vote = CompetitionRecordingVote.objects.get(votable=competition_recording, user=request.user)
                vote.delete()
                action.send(request.user, verb='retracted their recording tune', action_object=competition)
            except CompetitionRecordingVote.DoesNotExist:
                vote = CompetitionRecordingVote.objects.create(votable=competition_recording, user=request.user)
                action.send(request.user, verb='cast', action_object=vote)
            return redirect(competition.get_absolute_url())
    
    if request.method == 'POST' and 'submit-comment' in request.POST:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = CompetitionComment(
                        competition=competition, 
                        text=comment_form.cleaned_data['text'], 
                        author=request.user,
                        )
            comment.save()
            action.send(request.user, verb='made', action_object=comment, target=competition)
            return redirect(competition.get_absolute_url())
    else:
        comment_form = CommentForm()
    
    return render(request, 'archiver/competition.html', {
                            'competition': competition,
                            'user_tune_vote': competition.tune_vote(request.user),
                            'user_recording_vote': competition.recording_vote(request.user),
                            'recording_form': recording_form,
                            'comment_form': comment_form,
    })

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
            action.send(request.user, verb='submitted', action_object=tune)
            return redirect(tune.get_absolute_url())
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
            action.send(request.user, verb='submitted', action_object=recording)
            return redirect(recording.get_absolute_url())
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
            action.send(request.user, verb='submitted', action_object=event)
            return redirect(event.get_absolute_url())
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
                from_user_url = request.user.get_absolute_url()
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
        response['Content-Disposition'] = 'attachment; filename="machinefolksession_dataset_{}"'.format(now().strftime('%Y%m%d-%H%M%S'))
        return response
