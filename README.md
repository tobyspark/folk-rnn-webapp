# Folk RNN WebApp

The Folk RNN web app is in two parts: a composer for users to generate tunes using folkrnn, and an archiver to host and tweak them (and any other machine co-authored tunes). 

The web app is written in Python 3 using the Django framework. It uses the Channels architecture to handle websocket connections and a task queue. It uses the django-hosts middleware to route the composer and archiver apps on separate domains.

## Deployment

- Managed via [vagrant](http://vagrantup.com)
- OS: Ubuntu 16.04 LTS
	- This ships with Python 3.5
- To run on your laptop you need to install
	- vagrant
	- virtualbox
	- ...and nothing else, it's all contained and automatically set up within the VM.
- To deploy on a remote server, it's as above but we swap Linode's VPS service for VirtualBox.
	- vagrant
	- [vagrant linode plugin](https://github.com/displague/vagrant-linode)

### Procedure

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

### Procedure – Dev, i.e. local, VirtualBox
In a shell, navigate to the `folk-rnn-webapp` directory, and issue the following commands

```
vagrant up
vagrant ssh
/folk_rnn_webapp/runserver dev
```

On first run, `vagrant up` will download Ubuntu 16.04, create a VM and install the OS, and then run the configuration tasks, all as prescribed by the [Vagrantfile](https://github.com/tobyspark/folk-rnn-webapp/blob/master/Vagrantfile).

Thereafter, `vagrant up` will boot the machine, and `vagrant halt` will shut it down.

To get in, `vagrant ssh` and you should see your shell prompt change to `ubuntu@ubuntu`. Type `logout` or `<ctrl-d>` to close the ssh connection.

Once you have issued the runserver command, navigate to http://`127.0.0.1:8000` in your browser as it tells you. 

Note: Using the localhost IP address as above will route to the default app (currently the composer). To mimick real-world use and be able to access both apps typing e.g. `http://themachinefolksession.org.local:8000`, add the following to your `/etc/hosts` file. 
```
127.0.0.1	folkrnn.org.local
127.0.0.1	themachinefolksession.org.local
```

Note: if the specification for the VM changes, e.g. what's in the `Vagrantfile`, those changes will need to be retrospectively applied to any existing machines. Either `vagrant reload --provision` the existing machine, or `vagrant destroy; vagrant up` to create a fresh machine to this spec.

#### Backup, and restoring from it

A production install should automatically backup the database and key files to a cloud service.

A django management command is included to apply this backup to a local machine, i.e. follow the above procedure with this.

```
vagrant up
vagrant ssh
python3.6 /folk_rnn_webapp/folk_rnn_site/manage.py applybackup
```

#### Tests
```
vagrant up
vagrant ssh
cd /folk_rnn_webapp/folk_rnn_site/
pytest
```

### Procedure – Production, i.e. remote, Linode

Before starting you will need

- Linode API key
- ssh key configured

You will also want a sibling `folk_rnn_webapp` repository to keep dev and production separate (also a requirement of `vagrant`, which can’t handle a virtualbox VM and a remote Linode server simultaneously). So clone a fresh repo in addition to the above, adding a `production` suffix. You should have four folders like so
```
some-directory
├── folk-rnn
├── folk-rnn-webapp
├── folk-rnn-webapp-production
└── midi-js-soundfonts
```

In a shell, navigate to the `folk-rnn-webapp-production` directory. 

Create an environment file to configure the app for production. Create an `.env` file using `template.env`.

Issue the following commands

```
export LINODE_API_KEY=<your key here>
export FOLKRNN_PRODUCTION=foo
vagrant up --provider=linode
```

After some time, the server should be deployed and the webapp running (see note below).

As before, `vagrant ssh` to log in to the server, and `vagrant provision` to update. 

Note: there is a bug in `vagrant up` for the first time, the provisioning scripts that should run unprivileged instead run as root. However, rather than `vagrant destroy; vagrant up` to rebuild a machine, do this: `vagrant halt`, pause, `vagrant rebuild`, pause, `vagrant provision`. This will keep the IP address and provision correctly. So for a new server, do the rebuild dance and all should be good (alternatively, `chown vagrant:vagrant` the directory `/var/opt/folk_rnn_task/tune` and the contents of `/folk_rnn_static`).
