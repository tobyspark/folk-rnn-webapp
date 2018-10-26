from django.apps import AppConfig

class ArchiverConfig(AppConfig):
    name = 'archiver'
    
    def ready(self):
        from actstream import registry
        registry.register(self.get_model('User'))
        registry.register(self.get_model('Tune'))
        registry.register(self.get_model('TuneAttribution'))
        registry.register(self.get_model('Setting'))
        registry.register(self.get_model('TuneComment'))
        registry.register(self.get_model('Event'))
        registry.register(self.get_model('Recording'))
        registry.register(self.get_model('TuneRecording'))
        registry.register(self.get_model('TuneEvent'))
        registry.register(self.get_model('TunebookEntry'))
        registry.register(self.get_model('Competition'))
        registry.register(self.get_model('CompetitionComment'))
        registry.register(self.get_model('CompetitionTune'))
        registry.register(self.get_model('CompetitionTuneVote'))
        registry.register(self.get_model('CompetitionRecording'))
        registry.register(self.get_model('CompetitionRecordingVote'))
        
