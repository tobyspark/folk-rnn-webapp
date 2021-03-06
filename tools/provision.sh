#!/bin/bash

### Security, steps as per https://linode.com/docs/security/securing-your-server/

echo "***"
echo "*** Update Linux distro"
echo "***"
export DEBIAN_FRONTEND=noninteractive # https://askubuntu.com/questions/146921/how-do-i-apt-get-y-dist-upgrade-without-a-grub-config-prompt
apt-get update && apt-get upgrade --yes

echo "***"
echo "*** Check hostname"
echo "***"
if [ `hostname` != 'folkmachine' ]; then
    sudo hostnamectl set-hostname folkmachine
    echo '127.0.0.1 folkmachine' >> /etc/hosts
fi

echo "***"
echo "*** Check automatic updates"
echo "***"
apt-get install --yes unattended-upgrades

echo "***"
echo "*** Check SSH config"
echo "***"
if grep --regex='^PermitRootLogin yes' /etc/ssh/sshd_config; then
    sed -i.bak 's/^PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    systemctl restart sshd
fi
if grep --regex='^PasswordAuthentication yes' /etc/ssh/sshd_config; then
    sed -i.bak 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
    systemctl restart sshd
fi
if grep --regex='^AddressFamily inet$' /etc/ssh/sshd_config; then
    echo 'AddressFamily inet' | sudo tee -a /etc/ssh/sshd_config
    systemctl restart sshd
fi

echo "***"
echo "*** Check fail2ban"
echo "***"
apt-get install --yes fail2ban

echo "***"
echo "*** Check UFW"
echo "***"
ufw default deny incoming
ufw allow ssh
ufw allow http/tcp
ufw allow https/tcp
ufw --force enable
ufw status

echo "***"
echo "*** Check SSL Cert"
echo "***"

if [ ! -d /etc/letsencrypt ]; then
    apt-get install --yes software-properties-common
    add-apt-repository ppa:certbot/certbot
    apt-get update
    apt-get install --yes python-certbot-nginx
    certbot --non-interactive --nginx --agree-tos -m $LETSENCRYPT_ACCOUNT_EMAIL -d folkrnn.org -d www.folkrnn.org -d themachinefolksession.org -d www.themachinefolksession.org
fi
cp /folk_rnn_webapp/tools/systemd/letsencrypt.service /etc/systemd/system/letsencrypt.service
cp /folk_rnn_webapp/tools/systemd/letsencrypt.timer /etc/systemd/system/letsencrypt.timer
systemctl enable --now letsencrypt.timer