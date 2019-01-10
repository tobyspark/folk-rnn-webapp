import os
import tarfile
import logging
from tempfile import TemporaryDirectory

from django.core.management.base import BaseCommand
from django.core.management import call_command

from .backup import Command as BackupCommand

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """"
    Download the latest production backup and apply to local machine
    """
    help = 'Download the latest production backup and apply to local machine'

    def handle(self, *args, **kwargs):
        '''
        Process the command (i.e. the django manage.py entrypoint)
        '''
        logger.info('Apply Backup starting.')
        
        backup = BackupCommand()
        
        with TemporaryDirectory() as tmp:
            logger.info('Downloading latest production backup...')
            db_path, log_path, tunes_path = backup.download_latest_production_backup(to_dir=tmp)
            
            logger.info('Applying database...')
            with tarfile.open(name=db_path, mode='r:bz2') as tar:
                tar.extractall(path=tmp)
                call_command('flush', interactive=False) # Ideally drop, create and migrate
                                                         # sudo su -c postgres psql
                                                         # DROP DATABASE folk_rnn;
                                                         # CREATE DATABASE folk_rnn WITH OWNER=folk_rnn TEMPLATE=template0;
                                                         # python3.6 manage.py migrate
                call_command('loaddata', os.path.join(tmp, 'db_data.json'))
            
            logger.info('Applying logs...')
            with tarfile.open(name=log_path, mode='r:bz2') as tar:
                tar.extractall(path='/')
            
            logger.info('Applying tune...')
            with tarfile.open(name=tunes_path, mode='r:bz2') as tar:
                tar.extractall(path='/')
        
        logger.info('Apply Backup finished.')
