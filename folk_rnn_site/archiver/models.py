from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from embed_video.fields import EmbedVideoField

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
    def __str__(self):
        info = [f'MachineFolk {self.id}']
        if self.rnn_tune:
            info += [f'FolkRNN {self.rnn_tune.id}']
        return f'Tune: {self.title} ({", ".join(info)})'
    
    def clean(self):
        if self.check_valid_abc:
            # Ensure an X: header is present, needed for conform_abc
            self.header_x = 0
            # Validate ABC
            try:
                conform_abc(self.abc)
            except AttributeError as e:
                raise ValidationError({'abc': e})
        # Check there isn't already a tune with this abc body
        if any(x.body == self.body for x in Tune.objects.exclude(id=self.id)):
            raise ValidationError({'abc': 'This tune is not a variation of another.'})
        
    class Meta:
        ordering = ['id']
    
    @property 
    def valid_abc(self):
        try:
            conform_abc(self.abc)
            return True
        except:
            return False
    
    @property
    def title_or_mfsession(self):
        return self.title if len(self.title) else f'Untitled (Machine Folk Session №{self.id})' 
    
    author = models.ForeignKey(User, default=1)
    rnn_tune = models.ForeignKey(RNNTune, null=True, blank=True)
    check_valid_abc = models.BooleanField(default=True)
    submitted = models.DateTimeField(auto_now_add=True)

@receiver(post_save, sender=Tune)
def auto_x(sender, **kwargs):
    '''
    Update a tune's X: header to it's Machine Folk ID
    '''
    if kwargs['created']:
        instance = kwargs['instance']
        instance.header_x = instance.id
        # update db without recursive save signal
        sender.objects.filter(id=instance.id).update(abc=instance.abc)

class TuneAttribution(models.Model):
    def __str__(self):
        return f'Tune Meta: {self.text[:30]} (MachineFolk {self.tune.id})'
    
    class Meta:
        ordering = ['id']
        
    tune = models.ForeignKey(Tune)
    text = models.TextField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    
class Setting(ABCModel):
    def __str__(self):
        info = [f'X {self.header_x}', f'MachineFolk {self.tune.id}']
        if self.tune.rnn_tune:
            info += [f'FolkRNN {self.tune.rnn_tune.id}']
        return f'Setting: {self.title} ({", ".join(info)})'
    
    def clean(self):
        if self.check_valid_abc:
            # Ensure an X: header is present, needed for conform_abc
            self.header_x = 0
            # Validate ABC
            try:
                conform_abc(self.abc)
            except AttributeError as e:
                raise ValidationError({'abc': e})
        # Check the abc body is new
        if self.tune.body == self.body:
            raise ValidationError({'abc': 'This setting’s tune is not a variation on the main tune.'})
        # Check there isn't already a setting with this abc body
        if any(x.body == self.body for x in Setting.objects.exclude(id=self.id)):
            raise ValidationError({'abc': 'This setting is not a variation of another.'})
    
    class Meta:
        ordering = ['id']
    
    tune = models.ForeignKey(Tune)
    author = models.ForeignKey(User)
    check_valid_abc = models.BooleanField(default=True)
    submitted = models.DateTimeField(auto_now_add=True)

@receiver(post_save, sender=Setting)
def auto_x(sender, **kwargs):
    '''
    Update a setting's X: header to it's creation order
    '''
    if kwargs['created']:
        instance = kwargs['instance']
        settings = list(Setting.objects.filter(tune=instance.tune).order_by('id'))
        instance.header_x = settings.index(instance) + 1
        # update db without recursive save signal
        sender.objects.filter(id=instance.id).update(abc=instance.abc)

class Comment(models.Model):
    def __str__(self):
        return f'Comment: "{self.text[:30]}" by {self.author} on MachineFolk {self.tune.id})'
    
    class Meta:
        ordering = ['id']
        
    tune = models.ForeignKey(Tune)
    text = models.TextField(default='')
    author = models.ForeignKey(User)
    submitted = models.DateTimeField(auto_now_add=True)

class Documentation(models.Model):
    class Meta:
        abstract = True
        ordering = ['date', 'id']

    title = models.CharField(max_length=150)
    body = models.TextField()
    url = models.URLField(null=True, blank=True)
    date = models.DateField()
    author = models.ForeignKey(User)

class Event(Documentation):
    def __str__(self):
        return f'Event: {self.title[:30]}'
    
    image = models.ImageField(null=True, blank=True)

class Recording(Documentation):
    def __str__(self):
        return f'Recording: {self.title[:30]}'
    
    video = EmbedVideoField()
    event = models.ForeignKey(Event, null=True, blank=True)
        
class TuneRecording(models.Model):
    def __str__(self):
        return f'Tune Recording: {self.recording.title[:30]} (MachineFolk {self.tune.id})'
        
    class Meta:
        ordering = ['tune']

    tune = models.ForeignKey(Tune)
    recording = models.ForeignKey(Recording)

class TuneEvent(models.Model):
    def __str__(self):
        return f'Tune Event: {self.event.title[:30]} (MachineFolk {self.tune.id})'
    
    class Meta:
        ordering = ['tune']
    
    tune = models.ForeignKey(Tune)
    event = models.ForeignKey(Event)

class TunebookEntry(models.Model):
    def __str__(self):
        tune_str = f'MachineFolk {self.tune.id}' if self.tune else f'MachineFolk {self.setting.tune.id} Setting {self.setting.header_x}'
        return f'Tunebook Entry: {tune_str} by {self.user.get_full_name()}'
    
    @property
    def abc(self):
        if self.tune is not None:
            return self.tune.abc
        elif self.setting is not None:
            return self.setting.abc
        else:
            raise LookupError
    
    tune = models.ForeignKey(Tune, null=True)
    setting = models.ForeignKey(Setting, null=True)
    user = models.ForeignKey(User)
    submitted = models.DateTimeField(auto_now_add=True)
