# Folk RNN WebApp

## Dev VM info

- Managed via [vagrant](http://vagrantup.com)
- OS: Ubuntu 16.04 LTS
	- This ships with Python 3.5, i.e. before pip is bundled with python.

First run –

```
vagrant up
vagrant ssh

# install pip
sudo apt update
sudo apt install python-pip

# Oh no! folk-rnn is python 2 only, and doing any python 3 can screw up the dependencies installation.
#sudo apt install python3-pip
#sudo pip3 install --upgrade pip

# install folk-rnn
cd /vagrant_frnn
sudo pip install -e .
#no! sudo pip3 install -e .
```