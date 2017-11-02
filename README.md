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
From the repo root directory, do the following in a shell

```
vagrant up
vagrant ssh
/vagrant/runserver
```
and navigate to http://127.0.0.1:8000 in your browser

### Tests
```
vagrant up
vagrant ssh
python3 /vagrant/folk_rnn_site/manage.py test composer
python3 /vagrant/folk_rnn_site/manage.py test functional_tests
```