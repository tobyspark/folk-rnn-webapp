from django_hosts import patterns, host

host_patterns = patterns('',
    host(r'folkrnn\.org', 'composer.urls', name='composer'),
    host(r'themachinefolksession\.org', 'archiver.urls', name='archiver'),
)