# Folk RNN WebApp

## Dev VM info

- Managed via [vagrant](http://vagrantup.com)
- OS: Ubuntu 16.04 LTS
	- This ships with Python 3.5
- To run on your e.g. laptop you need to install
	- vagrant
	- virtualbox
	- ...and nothing else, it's all contained and automatically set up within the VM.

### Server
Create a directory on your host machine. Clone into that the following three repositories. Note the soundfont repository is optional, MIDI functionality will simply be hobbled without it.

- this _folk-rnn-webapp_, ie. `git clone https://github.com/tobyspark/folk-rnn-webapp.git`
- the _folk-rnn_ library, ie. `git clone https://github.com/tobyspark/folk-rnn.git`
- the _midi-js-soundfonts_ resources, ie. `git clone https://github.com/gleitz/midi-js-soundfonts.git`

You should have three folders like so
```
some-directory
├── folk-rnn
├── folk-rnn-webapp
└── midi-js-soundfonts
```

In a shell, navigate to the `folk-rnn-webapp` directory, and issue the following commands

```
vagrant up
vagrant ssh
/vagrant/runserver
```

On first run, `vagrant up` will download Ubuntu 16.04, create a VM and install the OS, and then run the configuration tasks, all as prescribed by the [Vagrantfile](https://github.com/tobyspark/folk-rnn-webapp/blob/master/Vagrantfile).

Thereafter, `vagrant up` will boot the machine, and `vagrant halt` will shut it down.

To get in, `vagrant ssh` and you should see your shell prompt change to `ubuntu@ubuntu`. Type `logout` or `<ctrl-d>` to close the ssh connection.

Once you have issued the runserver command,  navigate to http://127.0.0.1:8000 in your browser as it tells you.

Note: if the specification for the VM changes, e.g. what's in the `Vagrantfile`, those changes will need to be retrospectively applied to any existing machines. Either `vagrant reload --provision` the existing machine, or `vagrant destroy; vagrant up` to create a fresh machine to this spec.

### Tests
```
vagrant up
vagrant ssh
python3 /vagrant/folk_rnn_site/manage.py test composer
python3 /vagrant/folk_rnn_site/manage.py test functional_tests
```