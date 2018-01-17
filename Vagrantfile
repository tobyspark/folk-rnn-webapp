# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure("2") do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://vagrantcloud.com/search.
  config.vm.box = "ubuntu/xenial64"

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # NOTE: This will enable public access to the opened port
  # config.vm.network "forwarded_port", guest: 80, host: 8080

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine and only allow access
  # via 127.0.0.1 to disable public access
  config.vm.network "forwarded_port", guest: 8000, host: 8000, host_ip: "127.0.0.1"

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  config.vm.synced_folder "../folk-rnn", "/vagrant_frnn"
  config.vm.synced_folder "../midi-js-soundfonts/MusyngKite", "/vagrant_sf/soundfont"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  
  # FOLK RNN: uncomment this for basic VPS hosting spec
  # config.vm.provider "virtualbox" do |vb|
  #   # Customize the amount of memory on the VM:
  #   vb.memory = 1024
  #   vb.cpus = 1
  # end
  
  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  config.vm.provision "shell", inline: <<-SHELL
    apt-get update
    apt-get install --yes python3-pip
    pip3 install --upgrade pip
    # folk_rnn package
    cd /vagrant_frnn
    pip3 install -e .
    # folk_rnn models
    mkdir /var/opt/folk_rnn_task
    chown ubuntu:ubuntu /var/opt/folk_rnn_task
    su ubuntu -c /vagrant/tools/create_model_from_config_meta.py
    # folk_rnn webapp
    pip3 install "django<1.12"
    pip3 install "channels"
    apt-get install --yes redis-server
    pip3 install "asgi_redis"
    apt-get install --yes abcmidi
    # browser testing
    pip3 install "selenium<4"
    apt-get install --yes chromium-browser
    apt-get install --yes unzip
    apt-get install --yes libgconf-2-4
    wget --no-verbose https://chromedriver.storage.googleapis.com/2.33/chromedriver_linux64.zip
    unzip chromedriver*
    chmod +x chromedriver
    mv chromedriver /usr/local/bin/chromedriver
    rm chromedriver*
  SHELL
end
