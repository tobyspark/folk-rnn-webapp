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

  # Default to VirtualBox VM...
  config.vm.provider "virtualbox"

  # ...and have option to deploy to Linode VPS for production
  config.vm.provider :linode do |provider, override|
    override.ssh.username = 'vagrant'
    override.ssh.private_key_path = '~/.ssh/id_rsa'
    override.vm.box = 'linode'
    override.vm.box_url = 'https://github.com/displague/vagrant linode/raw/master/box/linode.box'
    override.vm.allowed_synced_folder_types = :rsync
    
    provider.label = 'folkmachine'
    provider.api_key = ENV['LINODE_API_KEY']
    provider.distribution = 'Ubuntu 16.04 LTS'
    provider.datacenter = 'london'
    provider.plan = 'Linode 1024'
  end
  
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
  config.vm.network "forwarded_port", guest: 8000, host: 8000, host_ip: "127.0.0.1" if not ENV['FOLKRNN_PRODUCTION']

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
  config.vm.synced_folder ".", "/folk_rnn_webapp", rsync__exclude: [".git", "folk_rnn_site/db.sqlite3"]
  config.vm.synced_folder "../folk-rnn", "/folk_rnn", rsync__exclude: ".git"
  config.vm.synced_folder "../midi-js-soundfonts/MusyngKite", "/folk_rnn_sf/soundfont", rsync__exclude: ".git"

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
  config.vm.provision "shell", path: "./tools/provision.sh"
  config.vm.provision "shell", path: "./tools/provision_folkrnn.sh"
  config.vm.provision "shell", path: "./tools/provision_tests.sh" if not ENV['FOLKRNN_PRODUCTION']
  config.vm.provision "shell", path: "./runserver", privileged:false if ENV['FOLKRNN_PRODUCTION']
end
