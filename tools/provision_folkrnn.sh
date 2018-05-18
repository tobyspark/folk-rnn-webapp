#!/bin/bash

echo "***"
echo "*** Check Folk RNN"
echo "***"

### Load environment
set -a; source /folk_rnn_webapp/.env; set +a

### Python provision

if [ ! -x /usr/local/bin/python3.6 ]; then
    apt-get install --yes build-essential checkinstall
    apt-get install --yes libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev
    wget --quiet https://www.python.org/ftp/python/3.6.4/Python-3.6.4.tar.xz
    tar xvf Python-3.6.4.tar.xz
    cd Python-3.6.4
    ./configure --enable-optimisation
    make altinstall # altinstall doesn't overwrite system python 
fi

### Folk RNN

# folk_rnn package
cd /folk_rnn
pip3.6 install -e .

# folk_rnn models
if [ ! -d /var/opt/folk_rnn_task ]; then
    mkdir /var/opt/folk_rnn_task
    chown vagrant:vagrant /var/opt/folk_rnn_task
    su vagrant -c /folk_rnn_webapp/tools/create_model_from_config_meta.py
fi

# folk_rnn webapp log dir
mkdir -p /var/log/folk_rnn_webapp
chown vagrant:vagrant /var/log/folk_rnn_webapp

# folk_rnn webapp static dir
mkdir -p /folk_rnn_static
chown vagrant:vagrant /folk_rnn_static

# folk_rnn webapp media dir
mkdir -p /folk_rnn_media
chown vagrant:vagrant /folk_rnn_media

# folk_rnn webapp packages
apt-get install --yes nginx
pip3.6 install "django<1.12"
pip3.6 install "django-hosts"
pip3.6 install "django-widget-tweaks"
pip3.6 install "channels~=2.0"
pip3.6 install "channels_redis"
pip3.6 install "pytest-django" "pytest-asyncio"
pip3.6 install psycopg2-binary
pip3.6 install google-api-python-client google-auth google-auth-httplib2

# See https://github.com/jazzband/django-embed-video/issues/87
# pip3.6 install django-embed-video
apt-get install --yes git
pip3.6 install git+https://github.com/tobyspark/django-embed-video.git

pip3.6 install django-markdown-deux
pip3.6 install pillow
apt-get install --yes postgresql
apt-get install --yes redis-server
apt-get install --yes abcmidi

# folk_rnn setup
cd /folk_rnn_webapp

# ...postgres setup
if ! su - postgres -c 'psql -l' | grep -q folk_rnn; then
    # Password auth for local users, i.e. unix user: vagrant, db user: folk_rnn
    su - postgres -c 'sed -i.bak "s/local   all             all                                     peer/local   all             all                                     md5/" /etc/postgresql/9.5/main/pg_hba.conf'
    sudo service postgresql restart
    cat << EOF | su - postgres -c psql
-- Create the database user:
CREATE USER folk_rnn WITH PASSWORD '${POSTGRES_PASS=dbpass}';
ALTER ROLE folk_rnn SET client_encoding TO 'utf8';
ALTER ROLE folk_rnn SET default_transaction_isolation TO 'read committed';
ALTER ROLE folk_rnn SET timezone TO 'UTC';
ALTER ROLE folk_rnn CREATEDB;
-- Create the database:
CREATE DATABASE folk_rnn WITH OWNER=folk_rnn TEMPLATE=template0;
EOF
fi

# ...nginx setup
for HOST in $COMPOSER_HOST $ARCHIVER_HOST; do
    cat ./tools/template.nginx.conf \
    | sed "s/kDOMAIN/$HOST/g" \
    | sed 's,kSOCKET,/folk_rnn_tmp/folk_rnn.org.socket,g' \
    | sed 's,kSTATIC,/folk_rnn_static,g' \
    | sed 's,kMEDIA,/folk_rnn_media,g' \
    > /etc/nginx/sites-available/$HOST
    sudo ln -sf /etc/nginx/sites-available/$HOST /etc/nginx/sites-enabled/$HOST
done

# ...nginx-daphne setup
mkdir -p /folk_rnn_tmp
chown vagrant:vagrant /folk_rnn_tmp

# ...systemd setup
cat ./tools/systemd/daphne.service \
| sed 's,kSOCKET,/folk_rnn_tmp/folk_rnn.org.socket,g' \
> /etc/systemd/system/daphne.service

cp ./tools/systemd/worker-folkrnn@.service /etc/systemd/system/worker-folkrnn@.service
cp ./tools/systemd/folkrnn-backup.service /etc/systemd/system/folkrnn-backup.service
cp ./tools/systemd/folkrnn-backup.timer /etc/systemd/system/folkrnn-backup.timer

systemctl enable nginx
systemctl enable daphne
systemctl enable redis-server
systemctl enable worker-folkrnn\@{1..1} # Worker numbers should scale with CPU cores.
systemctl enable --now folkrnn-backup.timer # Now as `runserver` won't start it.