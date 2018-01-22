#!/bin/bash

echo ***
echo *** Check Folk RNN
echo ***

### Python provision

apt-get install --yes python3-pip
pip3 install --upgrade pip

### Folk RNN

# folk_rnn package
cd /vagrant_frnn
pip3 install -e .

# folk_rnn models
if [ ! -d /var/opt/folk_rnn_task ]; then
    mkdir /var/opt/folk_rnn_task
    chown folkrnn:folkrnn /var/opt/folk_rnn_task
    su folkrnn -c /vagrant/tools/create_model_from_config_meta.py
fi

# folk_rnn webapp
pip3 install "django<1.12"
pip3 install "channels"
apt-get install --yes redis-server
pip3 install "asgi_redis"
apt-get install --yes abcmidi
