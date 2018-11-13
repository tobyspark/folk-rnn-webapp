from django.conf import settings
from archiver.models import Tune, Setting, Competition, CompetitionRecording, TuneComment, CompetitionComment, Collection, CollectionEntry, CompetitionTuneVote, CompetitionRecordingVote
from actstream import action, actions, registry

#Tune = apps.get_model('archiver', 'Tune')
registry.register(Tune)
folkrnn_anon_submission_default_author_id = 1
for tune in Tune.objects.all():
    if tune.author.id == folkrnn_anon_submission_default_author_id:
        continue
    actions.follow(tune.author, tune, actor_only=False, send_action=False)

#Setting = apps.get_model('archiver', 'Setting')
registry.register(Setting)
for setting in Setting.objects.all():
    actions.follow(setting.author, setting.tune, actor_only=False, send_action=False)

#Competition = apps.get_model('archiver', 'Competition')
registry.register(Competition)
#CompetitionRecording = apps.get_model('archiver', 'CompetitionRecording')
registry.register(CompetitionRecording)
for cr in CompetitionRecording.objects.all():
    actions.follow(cr.recording.author, cr.competition, actor_only=False, send_action=False)

#TuneComment = apps.get_model('archiver', 'TuneComment')
registry.register(TuneComment)
for tc in TuneComment.objects.all():
    actions.follow(tc.author, tc.tune, actor_only=False, send_action=False)

#CompetitionComment = apps.get_model('archiver', 'CompetitionComment')
registry.register(CompetitionComment)
for cc in CompetitionComment.objects.all():
    actions.follow(cc.author, cc.competition, actor_only=False, send_action=False)

#Collection = apps.get_model('archiver', 'Collection')
registry.register(Collection)
#CollectionEntry = apps.get_model('archiver', 'CollectionEntry')
registry.register(CollectionEntry)
for ce in CollectionEntry.objects.all():
    if ce.tune:
        actions.follow(ce.collection.user, ce.tune, actor_only=False, send_action=False)
    else:
        actions.follow(ce.collection.user, ce.setting, actor_only=False, send_action=False)

#CompetitionTuneVote = apps.get_model('archiver', 'CompetitionTuneVote')
registry.register(CompetitionTuneVote)
for ctv in CompetitionTuneVote.objects.all():
    actions.follow(ctv.user, ctv.votable.competition, actor_only=False, send_action=False)
    actions.follow(ctv.user, ctv.votable.tune, actor_only=False, send_action=False)

#CompetitionRecordingVote = apps.get_model('archiver', 'CompetitionRecordingVote')
registry.register(CompetitionRecordingVote)
for crv in CompetitionRecordingVote.objects.all():
    actions.follow(ctv.user, ctv.votable.competition, actor_only=False, send_action=False)
    actions.follow(crv.user, crv.votable.recording, actor_only=False, send_action=False)
