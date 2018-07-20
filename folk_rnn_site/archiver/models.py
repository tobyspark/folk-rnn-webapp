from django.db import models
from django.db.models.signals import post_save
from django.db.models import F, Count
from django.db.models.query import QuerySet
from django.dispatch import receiver
from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django_hosts.resolvers import reverse
from embed_video.fields import EmbedVideoField
from random import shuffle
from datetime import timedelta

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

class Tune(ABCModel):
    """
    A tune, e.g. the core data of /tune/x
    """
    def __str__(self):
        info = [f'MachineFolk {self.id}']
        if self.rnn_tune:
            info += [f'FolkRNN {self.rnn_tune.id}']
        return f'Tune: {self.title} ({", ".join(info)})'
    
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
    
    @property
    def abc_with_attribution(self):
        """"
        Return abc with attribution information fields
        - Sets (replacing) F: to the machinefolk URL
        - Sets (adding) S: to a machinefolk source message
        """
        url = reverse('tune', host='archiver', kwargs={'tune_id': self.id})
        abc_model = ABCModel(abc=self.abc)
        abc_model.headers_n = ['{} {}'.format(x.text if x.text else '', x.url if x.url else '') for x in self.tuneattribution_set.all()]
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
        tunebook__count=Count('tunebookentry', distinct=True),
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
        result.tunebook__count = result.tunebookentry_set.count()

def tune_queryset_annotate_saliency(self):
    """
    Annotate salience to Tune QuerySets that have already had salient counts annotated
    """
    return self.annotate(
        saliency = F('tunebook__count')*3 + F('setting__count')*3 + F('recording__count')*2 + F('event__count')*2 + F('comment__count')
    )
setattr(QuerySet, 'annotate_saliency', tune_queryset_annotate_saliency)

class TuneAttribution(models.Model):
    """
    An attribution item for a tune. Can record text, a URL, or both. 
    Multiple TuneAttributions can exist for any given tune.
    """
    def __str__(self):
        return f'Tune Meta: {self.text[:30]} (MachineFolk {self.tune.id})'
    
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
        info = [f'X {self.header_x}', f'MachineFolk {self.tune.id}']
        if self.tune.rnn_tune:
            info += [f'FolkRNN {self.tune.rnn_tune.id}']
        return f'Setting: {self.title} ({", ".join(info)})'
    
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
    
    @property
    def abc_with_attribution(self):
        """
        Return abc with attribution information fields
        - Sets (replacing) F: to the machinefolk URL
        - Sets (adding) S: to a machinefolk source message
        """
        url = reverse('tune', host='archiver', kwargs={'tune_id': self.tune.id})
        abc_model = ABCModel(abc=self.abc)
        abc_model.header_f = url
        s = f'Setting #{self.header_x} of tune #{self.tune.id} archived at The Machine Folk Session'
        if abc_model.header_s:
            s += '\nS:' + abc_model.header_s
        abc_model.header_s = s
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
        return f'Comment: "{self.text[:30]}" by {self.author} on MachineFolk {self.tune.id})'

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
        return f'Event: {self.title[:30]}'
    
    image = models.ImageField(null=True, blank=True)

class Recording(Documentation):
    """
    A recording.
    Handles Youtube, Vimeo videos and SoundCloud audio tracks.
    """
    def __str__(self):
        return f'Recording: {self.title[:30]}'
    
    video = EmbedVideoField()
    event = models.ForeignKey(Event, null=True, blank=True)
        
class TuneRecording(models.Model):
    """
    Assign a recording to a tune.
    """
    def __str__(self):
        return f'Tune Recording: {self.recording.title[:30]} (MachineFolk {self.tune.id})'
        
    class Meta:
        ordering = ['tune']

    tune = models.ForeignKey(Tune)
    recording = models.ForeignKey(Recording)

class TuneEvent(models.Model):
    """
    Assign an event to a tune.
    """
    def __str__(self):
        return f'Tune Event: {self.event.title[:30]} (MachineFolk {self.tune.id})'
    
    class Meta:
        ordering = ['tune']
    
    tune = models.ForeignKey(Tune)
    event = models.ForeignKey(Event)

class TunebookEntry(models.Model):
    """
    Assign a tune or setting to a user, creating a tunebook.
    """
    def __str__(self):
        tune_str = f'MachineFolk {self.tune.id}' if self.tune else f'MachineFolk {self.setting.tune.id} Setting {self.setting.header_x}'
        return f'Tunebook Entry: {tune_str} by {self.user.get_full_name()}'
    
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
    user = models.ForeignKey(User)
    submitted = models.DateTimeField(auto_now_add=True)

class Competition(models.Model):
    """
    Vote upon a tune and subsequently vote on uploaded recordings of it. 
    A community engagement, 'Tune of the Month'.
    # FIXME: The dates are UTC, and that's misleading for UTC+1 in summer time London let alone New Zealand.
    """
    title = models.CharField(max_length=150)
    text = models.TextField(help_text='This is a markdown field, e.g. *italics* and [a link](http://tobyz.net)')
    author = models.ForeignKey(User)
    tune_vote_open = models.DateField()
    recording_submit_open = models.DateField()
    recording_vote_open = models.DateField()
    recording_vote_close = models.DateField()
    
    def __str__(self):
        return f'Competition {self.id}: {self.title}'
    
    def clean(self):
        if self.tune_vote_open >= self.recording_submit_open:
            raise ValidationError({'recording_submit_open': 'Submission can only start after tune has been selected'})
        if self.recording_submit_open > self.recording_vote_open:
            raise ValidationError({'recording_vote_open': 'Voting can only start on or after the day submissions start'})
        if self.recording_vote_open > self.recording_vote_close:
            raise ValidationError({'recording_vote_close': 'Voting needs to finish on or after the day it starts'})
    
    @property
    def tune_vote_close(self):
        return self.recording_submit_open - timedelta(days=1)
    
    @property
    def recording_submit_close(self):
        # recording_vote_close rather than _open keeps submission open during voting 
        # seems more in the spirit of making music vs. being on podium
        return self.recording_vote_close 
    
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
        if today > self.recording_submit_close:
            return 'AFTER'
        return 'IN'
    
    @property
    def recording_voting_state(self):
        today = now().date()
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
        except CompetitionTune.DoesNotExist:
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
        except CompetitionRecording.DoesNotExist:
            return None

class CompetitionComment(Comment):
    """
    A comment upon a competition.
    Multiple comments can exist for any given compeition.
    """
    def __str__(self):
        return f'Comment: "{self.text[:30]}" by {self.author} on Competition {self.competition.title})'

    competition = models.ForeignKey(Competition, related_name='comment_set', related_query_name='comment')

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
        return f'Competition tune {self.tune.id} for {self.competition.id}: {self.competition.title}'

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
        return f'Competition recording {self.recording.id} for {self.competition.id}: {self.competition.title}'
    
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
