from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
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
    submitted = models.DateTimeField(auto_now_add=True)

class TuneAttribution(models.Model):
    def __str__(self):
        return f'Tune Meta: {self.text[:30]} (MachineFolk {self.tune.id})'
    
    class Meta:
        ordering = ['id']
        
    tune = models.ForeignKey(Tune)
    text = models.TextField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    
class SettingManager(models.Manager):
    def create_setting(self, tune, abc, author):
        # Create but don't add to db
        setting = Setting(tune=tune, abc=abc, author=author)
        setting.header_x = self.filter(tune=tune).count() + 1
        # Validate ABC
        conform_abc(setting.abc)
        # Check the abc body is new
        if tune.body == setting.body:
            raise ValueError('This setting is not a variation on the main tune.')
        # Check there isn't already a setting with this abc body
        if any(x.body == setting.body for x in self.all()):
            raise ValueError('This setting is not a variation on another setting’s tune.')
        # Check it has a new, unique title
        if setting.title.startswith(FOLKRNN_TUNE_TITLE_CLIENT):
            raise ValueError('This setting still has the (machine generated) title of the original tune.')
        if any(x.title == setting.title for x in Tune.objects.exclude(id=tune.id)):
            raise ValueError('This setting has the title of an existing (machine generated) tune.')
        if any(x.title == setting.title for x in self.all()):
            raise ValueError('This setting has the title of another setting.')
        # Now verified, add to db
        setting.save()
        return setting

class Setting(ABCModel):
    def __str__(self):
        info = [f'X {self.header_x}', f'MachineFolk {self.tune.id}']
        if self.tune.rnn_tune:
            info += [f'FolkRNN {self.tune.rnn_tune.id}']
        return f'Setting: {self.title} ({", ".join(info)})'
    
    class Meta:
        ordering = ['id']
    
    tune = models.ForeignKey(Tune)
    author = models.ForeignKey(User)
    submitted = models.DateTimeField(auto_now_add=True)

    objects = SettingManager()

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
