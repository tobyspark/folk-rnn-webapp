from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from archiver.models import (
                        User, 
                        Tune, 
                        TuneAttribution, 
                        TuneRecording, 
                        TuneEvent, 
                        Setting, 
                        TuneComment, 
                        Recording, 
                        Event,
                        Competition,
                        CompetitionTune,
                        CompetitionTuneVote,
                        CompetitionRecording,
                        CompetitionRecordingVote,
                        CompetitionComment,
                        )

admin.site.site_header = "Administration – The Machine Folk Session"
admin.site.site_title = "Administration – The Machine Folk Session"

class TuneAttributionInline(admin.StackedInline):
    model = TuneAttribution

class SettingInline(admin.StackedInline):
    model = Setting
     
class TuneCommentInline(admin.StackedInline):
    model = TuneComment

class TuneRecordingInline(admin.StackedInline):
    model = TuneRecording

class TuneEventInline(admin.StackedInline):
    model = TuneEvent

class CompetitionTuneInline(admin.StackedInline):
    model = CompetitionTune
    
class CompetitionTuneVoteInline(admin.StackedInline):
    model = CompetitionTuneVote
    
class CompetitionRecordingInline(admin.StackedInline):
    model = CompetitionRecording
    
class CompetitionRecordingVoteInline(admin.StackedInline):
    model = CompetitionRecordingVote
    
class CompetitionCommentInline(admin.StackedInline):
    model = CompetitionComment

@admin.register(Tune)
class TuneAdmin(admin.ModelAdmin):
    inlines = [ TuneAttributionInline, SettingInline, TuneCommentInline, TuneEventInline, TuneRecordingInline ]

@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    inlines = [ TuneRecordingInline ]

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    inlines = [ TuneEventInline ]

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Define admin model for User with email address as username
    """

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'date_joined', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    inlines = [ CompetitionTuneInline, CompetitionCommentInline ]

@admin.register(CompetitionTune)
class CompetitionTuneAdmin(admin.ModelAdmin):
    inlines = [ CompetitionTuneVoteInline ]

@admin.register(CompetitionRecording)
class CompetitionRecordingAdmin(admin.ModelAdmin):
    inlines = [ CompetitionRecordingVoteInline ]