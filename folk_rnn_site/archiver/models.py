from django.db import models
from django.db.models.signals import post_save
from django.db.models import F, Count
from django.db.models.query import QuerySet
from django.dispatch import receiver
from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.urls import reverse
from embed_video.fields import EmbedVideoField
from random import shuffle
from datetime import timedelta
from textwrap import shorten

from folk_rnn_site.models import ABCModel, conform_abc
from composer.models import RNNTune
from composer import FOLKRNN_TUNE_TITLE_CLIENT

class UserManager(BaseUserManager):
    """
    Manager for User model with email address as the username
    https://www.fomfus.com/articles/how-to-use-email-as-username-for-django-authentication-removing-the-username
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    """
    User, with email address as the username
    https://www.fomfus.com/articles/how-to-use-email-as-username-for-django-authentication-removing-the-username
    https://github.com/django/django/blob/stable/1.11.x/django/contrib/auth/models.py#L299
    """
    username = None
    email = models.EmailField('email address', unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    def __str__(self):
        name = self.get_full_name()
        return f'{name} ({self.id})'
    
    def get_absolute_url(self):
        return reverse('user', kwargs={'user_id': self.id})
    
    @property
    def tunebook(self):
        tunebook, created = Collection.objects.get_or_create(user=self)
        return tunebook

class Tune(ABCModel):
    """
    A tune, e.g. the core data of /tune/x
    """
    def __str__(self):
        info = [f'mf:{self.id}']
        if self.rnn_tune:
            info += [f'frnn:{self.rnn_tune.id}']
        return f'{self.title} ({", ".join(info)})'
    
    def clean(self):
        """
        Checks ABC is valid if desired
        Checks there isn't already a tune with this abc body
        """
        if self.check_valid_abc:
            try:
                conform_abc(self.abc)
            except AttributeError as e:
                raise ValidationError({'abc': e})
        if any(x.body == self.body for x in Tune.objects.exclude(id=self.id)):
            raise ValidationError({'abc': 'This tune is not a variation of another.'})
        
    class Meta:
        ordering = ['id']
    
    def get_absolute_url(self):
        return reverse('tune', kwargs={'tune_id': self.id})
    
    @property
    def abc_with_attribution(self):
        """"
        Return abc with attribution information fields
        """
        url = self.get_absolute_url()
        abc_model = ABCModel(abc=self.abc)
        abc_model.headers_n = ['{} {}'.format(x.text if x.text else '', x.url if x.url else '') for x in self.tuneattribution_set.all()]
        if self.rnn_tune:
            model = self.rnn_tune.rnn_model_name.replace('.pickle', '')
            abc_model.headers_n += [ f'Generated at https://folkrnn.org using the { model } model with RNN seed = { self.rnn_tune.seed }; temperature = { self.rnn_tune.temp }; prime tokens = { self.rnn_tune.prime_tokens }' ]
        abc_model.header_f = url
        abc_model.header_s = f'Tune #{self.id} archived at The Machine Folk Session'
        return abc_model.abc
    
    author = models.ForeignKey(User, default=1)
    rnn_tune = models.ForeignKey(RNNTune, null=True, blank=True)
    check_valid_abc = models.BooleanField(default=True)
    submitted = models.DateTimeField(auto_now_add=True)

@receiver(post_save, sender=Tune)
def tune_post_save(sender, **kwargs):
    """"
    Update a tune's X: header to it's Machine Folk ID
    Ensure a tune has a title
    Create TuneAttributions from relevant ABC information fields, removing them in the process.
    """
    # update X
    instance = kwargs['instance']
    instance.header_x = instance.id
    
    # ensure T
    if not instance.title:
        instance.title = f'Untitled (Machine Folk Session №{instance.id})' 
    
    # extract attributions
    for field in instance.headers_n:
        attribution = TuneAttribution.objects.create(
                                tune = instance,
                                text = field,
                                url = None,
                        )
    instance.headers_n = None
    while instance.header_s:
        attribution = TuneAttribution.objects.create(
                                tune = instance,
                                text = instance.header_s,
                                url = None,
                        )
        instance.header_s = None
    while instance.header_f:
        attribution = TuneAttribution.objects.create(
                                tune = instance,
                                text = 'As submitted:',
                                url = instance.header_f,
                        )
        instance.header_f = None

    # update db without recursive save signal
    sender.objects.filter(id=instance.id).update(abc=instance.abc)

def tune_queryset_annotate_counts(self):
    """
    Annotate salient counts to Tune QuerySets
    """
    return self.annotate(
        Count('setting', distinct=True), 
        Count('comment', distinct=True), 
        recording__count=Count('tunerecording', distinct=True), 
        event__count=Count('tuneevent', distinct=True),
        collection__count=Count('collectionentry', distinct=True),
    )
setattr(QuerySet, 'annotate_counts', tune_queryset_annotate_counts)

def annotate_counts(tunes):
    """
    Annotate salient counts to Tune lists
    This is the equivalent of tune_queryset_annotate_counts for when no longer a QuerySet
    """
    for result in tunes:
        result.setting__count = result.setting_set.count()
        result.comment__count = result.comment_set.count() 
        result.recording__count = result.tunerecording_set.count() 
        result.event__count = result.tuneevent_set.count()
        result.collection__count = result.collectionentry_set.count()

def tune_queryset_annotate_saliency(self):
    """
    Annotate salience to Tune QuerySets that have already had salient counts annotated
    """
    return self.annotate(
        saliency = F('collection__count')*3 + F('setting__count')*3 + F('recording__count')*2 + F('event__count')*2 + F('comment__count')
    )
setattr(QuerySet, 'annotate_saliency', tune_queryset_annotate_saliency)

class TuneAttribution(models.Model):
    """
    An attribution item for a tune. Can record text, a URL, or both. 
    Multiple TuneAttributions can exist for any given tune.
    """
    def __str__(self):
        return f'{shorten(self.text, width=30)} (mf:{self.tune.id})'
    
    class Meta:
        ordering = ['id']
        
    tune = models.ForeignKey(Tune)
    text = models.TextField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    
class Setting(ABCModel):
    """
    A setting of a tune, e.g. a (probably human) development of the (probably machine generated) source tune.
    Multiple settings can exist for any given tune.
    """
    def __str__(self):
        info = [f'setting:{self.header_x}', f'mf:{self.tune.id}']
        if self.tune.rnn_tune:
            info += [f'frnn:{self.tune.rnn_tune.id}']
        return f'{self.title} ({", ".join(info)})'
    
    def clean(self):
        """
        Checks ABC is valid if desired
        Checks the ABC is a variant of the original tune
        Checks there isn't already a setting with this ABC
        """
        if self.check_valid_abc:
            try:
                conform_abc(self.abc)
            except AttributeError as e:
                raise ValidationError({'abc': e})
        if self.tune.abc_tune_fingerprint == self.abc_tune_fingerprint:
            raise ValidationError({'abc': 'This setting’s tune is not a variation on the main tune.'})
        if any(x.abc_tune_fingerprint == self.abc_tune_fingerprint for x in Setting.objects.exclude(id=self.id)):
            raise ValidationError({'abc': 'This setting is not a variation of another.'})
    
    class Meta:
        ordering = ['id']
    
    def get_absolute_url(self):
        return reverse('setting', kwargs={'tune_id': self.tune.id, 'setting_id': self.header_x})
    
    @property
    def abc_with_attribution(self):
        """
        Return abc with attribution information fields
        """
        url = self.get_absolute_url()
        abc_model = ABCModel(abc=self.abc)
        if self.tune.rnn_tune:
            model = self.tune.rnn_tune.rnn_model_name.replace('.pickle', '')
            abc_model.headers_n = [ f'Original tune generated at https://folkrnn.org using the { model } model with RNN seed = { self.tune.rnn_tune.seed }; temperature = { self.tune.rnn_tune.temp }; prime tokens = { self.tune.rnn_tune.prime_tokens }' ]
        abc_model.header_f = url
        abc_model.header_s = f'Setting #{self.header_x} of tune #{self.tune.id} archived at The Machine Folk Session'
        
        return abc_model.abc
    
    tune = models.ForeignKey(Tune)
    author = models.ForeignKey(User)
    check_valid_abc = models.BooleanField(default=True)
    submitted = models.DateTimeField(auto_now_add=True)

@receiver(post_save, sender=Setting)
def setting_auto_x(sender, **kwargs):
    """
    Update a setting's X: header to it's creation order
    """
    instance = kwargs['instance']
    settings = list(Setting.objects.filter(tune=instance.tune).order_by('id'))
    instance.header_x = settings.index(instance) + 1
    # update db without recursive save signal
    sender.objects.filter(id=instance.id).update(abc=instance.abc)

class Comment(models.Model):
    """
    Abstract base class for comment models
    """
    
    class Meta:
        abstract = True
        ordering = ['id']
        
    text = models.TextField(default='')
    author = models.ForeignKey(User)
    submitted = models.DateTimeField(auto_now_add=True)

class TuneComment(Comment):
    """
    A comment upon a tune.
    Multiple comments can exist for any given tune.
    """
    def __str__(self):
        return f'"{shorten(self.text, width=30)}" by {self.author} on tune {self.tune})'
    
    def get_absolute_url(self):
        tune_url = reverse('tune', kwargs={'tune_id': self.tune.id})
        return f'{tune_url}#comments'

    tune = models.ForeignKey(Tune, related_name='comment_set', related_query_name='comment')

class Documentation(models.Model):
    """
    Abstract base class for documentation models
    """
    class Meta:
        abstract = True
        ordering = ['date', 'id']

    title = models.CharField(max_length=150)
    body = models.TextField()
    url = models.URLField(null=True, blank=True)
    date = models.DateField()
    author = models.ForeignKey(User)

class Event(Documentation):
    """
    An event, e.g. a concert or session
    """
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('event', kwargs={'event_id': self.id})
    
    image = models.ImageField(null=True, blank=True)

class Recording(Documentation):
    """
    A recording.
    Handles Youtube, Vimeo videos and SoundCloud audio tracks.
    """
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('recording', kwargs={'recording_id': self.id})
    
    video = EmbedVideoField()
    event = models.ForeignKey(Event, null=True, blank=True)
        
class TuneRecording(models.Model):
    """
    Assign a recording to a tune.
    """
    def __str__(self):
        return f'{self.recording.title} of tune {self.tune})'
        
    class Meta:
        ordering = ['tune']

    tune = models.ForeignKey(Tune)
    recording = models.ForeignKey(Recording)

class TuneEvent(models.Model):
    """
    Assign an event to a tune.
    """
    def __str__(self):
        return f'{self.event.title} of tune {self.tune})'
    
    class Meta:
        ordering = ['tune']
    
    tune = models.ForeignKey(Tune)
    event = models.ForeignKey(Event)

class Collection(models.Model):
    """
    A collection, a tunebook when user property is filled
    """
    def __str__(self):
        return f'Tunebook – {self.user}' if self.user else f'Collection (mf:{self.id})'
    
    def get_absolute_url(self):
        if self.user is not None:
            return reverse('tunebook', kwargs={'user_id': self.user.id})
        return None
    
    user = models.ForeignKey(User, null=True)

class CollectionEntry(models.Model):
    """
    Assign a tune or setting to a collection.
    """
    def __str__(self):
        tune_str = f'{self.tune}' if self.tune else f'{self.setting}'
        return f'{tune_str} in {self.collection}'
    
    @property
    def abc(self):
        """
        Return the expected abc whether tune or setting
        """
        if self.tune is not None:
            return self.tune.abc
        elif self.setting is not None:
            return self.setting.abc
        else:
            raise LookupError

    @property
    def abc_with_attribution(self):
        """
        Return the expected abc_with_attribution whether tune or setting
        """
        if self.tune is not None:
            return self.tune.abc_with_attribution
        elif self.setting is not None:
            return self.setting.abc_with_attribution
        else:
            raise LookupError
    
    tune = models.ForeignKey(Tune, null=True)
    setting = models.ForeignKey(Setting, null=True)
    collection = models.ForeignKey(Collection)
    submitted = models.DateTimeField(auto_now_add=True)

class Competition(models.Model):
    """
    Vote upon a tune and upload recordings of the winning tune.
    Optionally vote upon the recordings.
    e.g. A community engagement, 'Tune of the Month'.
    """
    title = models.CharField(max_length=150)
    text = models.TextField(help_text='This is a markdown field, e.g. *italics* and [a link](http://tobyz.net)')
    author = models.ForeignKey(User)
    tune_vote_open = models.DateField()
    recording_submit_open = models.DateField()
    recording_vote_open = models.DateField(blank=True, null=True, help_text='Optional, if voting on the recordings is desired.')
    recording_vote_close = models.DateField(blank=True, null=True, help_text='Optional, if voting on the recordings is desired.')
    
    def __str__(self):
        return self.title
    
    def clean(self):
        if self.tune_vote_open >= self.recording_submit_open:
            raise ValidationError({'recording_submit_open': 'Submission can only start after tune has been selected'})
        if self.recording_vote_open is None:
            return 
        if self.recording_submit_open > self.recording_vote_open:
            raise ValidationError({'recording_vote_open': 'Voting can only start on or after the day submissions start'})
        if self.recording_vote_close is None:
            raise ValidationError({'recording_vote_close': 'Close value is required if recordings are voted upon'})
        if self.recording_vote_open > self.recording_vote_close:
            raise ValidationError({'recording_vote_close': 'Voting needs to finish on or after the day it starts'})
    
    
    def get_absolute_url(self):
        return reverse('competition', kwargs={'competition_id': self.id})
    
    @property
    def tune_vote_close(self):
        return self.recording_submit_open - timedelta(days=1)
    
    @property
    def recording_submit_close(self):
        if self.recording_vote_close:
            # if there is going to be a recording vote, close submission either before recording vote opens or closes.
            # _close rather than _open keeps submission open during voting seems more in the spirit of making music vs. being on podium
            return self.recording_vote_close
        return None
    
    @property
    def tune_voting_state(self):
        today = now().date()
        if today < self.tune_vote_open:
            return 'BEFORE'
        if today > self.tune_vote_close:
            return 'AFTER'
        return 'IN'
    
    @property
    def recording_submission_state(self):
        today = now().date()
        if today < self.recording_submit_open:
            return 'BEFORE'
        if self.recording_submit_close and today > self.recording_submit_close:
            return 'AFTER'
        return 'IN'
    
    @property
    def recording_voting_state(self):
        today = now().date()
        if self.recording_vote_open is None:
            return None
        if today < self.recording_vote_open:
            return 'BEFORE'
        if today > self.recording_vote_close:
            return 'AFTER'
        return 'IN'
        
    @property
    def tune_set(self):
        """
        A shuffled queryset of the tunes in this competition, with vote count
        """
        tunes = list(
                    Tune.objects
                    .filter(competitiontune__competition=self)
                    .annotate(votes=Count('competitiontune__vote'))
                    )
        shuffle(tunes) # Note can't use .order_by('?') with annotations, get duplicate rows
        return tunes
    
    @property
    def recording_set(self):
        """
        A shuffled queryset of the recordings in this competition, with vote count
        """
        recordings = list(
                        Recording.objects
                        .filter(competitionrecording__competition=self)
                        .annotate(votes=Count('competitionrecording__vote'))
                        )
        shuffle(recordings)
        return recordings
    
    @property
    def competition_tune_won(self):
        """
        The CompetitionTune that received the most votes
        """
        return (
                CompetitionTune.objects
                .filter(competition=self)
                .annotate(votes=Count('vote'))
                .latest('votes')
                )
    
    @property
    def tune_won(self):
        """
        The Tune that received the most votes
        """
        return self.competition_tune_won.tune
    
    @property
    def competition_recording_won(self):
        """
        The CompetitionRecording that received the most votes
        """
        return (
                CompetitionRecording.objects
                .filter(competition=self)
                .annotate(votes=Count('vote'))
                .latest('votes')
                )
    
    @property
    def recording_won(self):
        """
        The Recording that received the most votes
        """
        return self.competition_recording_won.recording
    
    def tune_vote(self, user):
        """
        The tune the user has voted for, if any
        """
        try:
            return (
                    CompetitionTune.objects
                    .filter(competition=self)
                    .filter(vote__user=user)
                    .get().tune
                    )
        except (CompetitionTune.DoesNotExist, TypeError):
            return None
    
    def recording_vote(self, user):
        """
        The recording the user has voted for, if any
        """
        try:
            return (
                    CompetitionRecording.objects
                    .filter(competition=self)
                    .filter(vote__user=user)
                    .get().recording
                    )
        except (CompetitionRecording.DoesNotExist, TypeError):
            return None

class CompetitionComment(Comment):
    """
    A comment upon a competition.
    Multiple comments can exist for any given compeition.
    """
    def __str__(self):
        return f'"{shorten(self.text, width=30)}" by {self.author} on {self.competition})'

    competition = models.ForeignKey(Competition, related_name='comment_set', related_query_name='comment')
    
    def get_absolute_url(self):
        return f'{self.competition.get_absolute_url()}#comments'

class VoteModel(models.Model):
    """
    Abstract base class for a vote object. Make concrete with the following field:
    votable = models.ForeignKey(<VotableModel>, related_name='vote_set', related_query_name='vote')
    """
    class Meta:
        abstract = True
        unique_together = ('user', 'votable')
        
    user = models.ForeignKey(User)
    submitted = models.DateTimeField(auto_now_add=True)
        
class CompetitionTune(models.Model):
    """
    A tune, one of e.g. 5, that can be voted on to select the tune people will learn and record
    """
    competition = models.ForeignKey(Competition)
    tune = models.ForeignKey(Tune)
    
    def __str__(self):
        return f'{self.tune} for {self.competition}'

class CompetitionTuneVote(VoteModel):
    """
    A vote, hopefully one of many, upon a competition tune
    """
    votable = models.ForeignKey(CompetitionTune, related_name='vote_set', related_query_name='vote')

class CompetitionRecording(models.Model):
    """
    A recording that can be voted on to select the most favoured rendition of the winning tune
    """
    competition = models.ForeignKey(Competition)
    recording = models.ForeignKey(Recording)
    
    def __str__(self):
        return f'{self.recording} for {self.competition}'
    
    def clean(self):
        """
        Check the recording is a recording of the winning tune
        """
        if not self.recording.tunerecording_set.filter(tune=self.competition.tune_won).exists():
            raise ValidationError({'recording': 'This is not a recording of the winning tune'})

class CompetitionRecordingVote(VoteModel):
    """
    A vote, hopefully one of many, upon a competition recording
    """
    votable = models.ForeignKey(CompetitionRecording, related_name='vote_set', related_query_name='vote')
