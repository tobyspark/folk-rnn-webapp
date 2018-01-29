#!/bin/bash

echo ***
echo *** Check Folk RNN
echo ***

### Load environment
set -a; source /folk_rnn_webapp/.env; set +a

### Python provision

apt-get install --yes python3-pip
pip3 install --upgrade pip

### Folk RNN

# folk_rnn package
cd /folk_rnn
pip3 install -e .

# folk_rnn models
if [ ! -d /var/opt/folk_rnn_task ]; then
    mkdir /var/opt/folk_rnn_task
    chown vagrant:vagrant /var/opt/folk_rnn_task
    su vagrant -c /folk_rnn_webapp/tools/create_model_from_config_meta.py
fi

# folk_rnn webapp static dir
mkdir -p /folk_rnn_static
chown vagrant:vagrant /folk_rnn_static

# folk_rnn webapp packages
apt-get install --yes nginx
pip3 install "django<1.12"
pip3 install "channels"
apt-get install --yes redis-server
pip3 install "asgi_redis"
apt-get install --yes abcmidi

# folk_rnn setup
cd /folk_rnn_webapp

# ...nginx setup
cat ./tools/template.nginx.conf \
| sed "s/kDOMAIN/$DJANGO_ALLOWED_HOSTS/g" \
| sed 's,kSOCKET,/folk_rnn_tmp/folk_rnn.org.socket,g' \
| sed 's,kSTATIC,/folk_rnn_static,g' \
> /etc/nginx/sites-available/folk_rnn.org
sudo ln -sf /etc/nginx/sites-available/folk_rnn.org /etc/nginx/sites-enabled/folk_rnn.org

# ...nginx-daphne setup
mkdir -p /folk_rnn_tmp
chown vagrant:vagrant /folk_rnn_tmp

# ...systemd setup
cat ./tools/systemd/daphne.service \
| sed 's,kSOCKET,/folk_rnn_tmp/folk_rnn.org.socket,g' \
> /etc/systemd/system/daphne.service

cp ./tools/systemd/worker-all@.service /etc/systemd/system/worker-all@.service
cp ./tools/systemd/worker-http@.service /etc/systemd/system/worker-http@.service

systemctl enable nginx
systemctl enable daphne
systemctl enable redis-server
systemctl enable worker-http\@{1..1} # Worker numbers should scale with CPU cores.
systemctl enable worker-all\@{1..1}