#!/usr/local/bin/python3.6

import os
import time
import tarfile
import logging
from io import BytesIO, TextIOWrapper
from tempfile import SpooledTemporaryFile

import apiclient
from google.oauth2 import service_account

from django.core.management.base import BaseCommand
from django.core.management import call_command

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'folkrnn-gdrive.json'

logger = logging.getLogger(__name__)

def backup_suffix():
    timestamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    server = 'production' if 'FOLKRNN_PRODUCTION' in os.environ else 'dev'
    return f'_backup_{server}_{timestamp}'

class Command(BaseCommand):
    """"
    Backup management using Google Drive. A Django management command.
    i.e `python3.6 /vagrant/folk_rnn_webapp/folk_rnn_site/manage.py backup`
    
    Note: the Google accreditation is not user authorised, so these files will not be visible to the user in Google Drive.
    https://developers.google.com/api-client-library/python/auth/service-accounts

    Includes utility functions, typically for interactive use, i.e.
        cd /folk_rnn_webapp/folk_rnn_site
        python3.6
        from backup.management.commands.backup import Command
        backup = Command()
        backup.list_stored_files()
    """
    help = 'Archives folkrnn and machinefolksession data in Google Drive'
    
    def __init__(self):
        # Establish Google Drive client
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        self.drive = apiclient.discovery.build('drive', 'v3', credentials=credentials)
    
    def handle(self, *args, **kwargs):
        '''
        Process the command (i.e. the django manage.py entrypoint)
        '''
        logger.info('Backup starting.')
        
        logger.info('Backing up tunes...')
        self.archive_store_folder('/var/opt/folk_rnn_task/tunes')
        logger.info('Backing up logs...')
        self.archive_store_folder('/var/log/folk_rnn_webapp/')
        logger.info('Backing up database...')
        self.archive_store_database()
        
        logger.info("Backup completed.")
    
    def archive_store_database(self):
        """
        Archive and store in Google Drive the contents of the folder (recursively)
        Returns name of uploaded file
        """
        data = BytesIO()
        call_command('dumpdata', all=True, format='json', stdout=TextIOWrapper(data))
        with SpooledTemporaryFile() as f:
            # Archive to tar
            with tarfile.open(fileobj=f, mode='x:bz2') as tar:
                info = tarfile.TarInfo('db_data.json')
                info.size = data.tell()
                data.seek(0)
                tar.addfile(info, data)
            data.close()
            # Store in Google Drive
            body = {
                'name': 'db_data' + backup_suffix() + '.tar.gz',
                }
            media_body = apiclient.http.MediaIoBaseUpload(f, 
                                            mimetype='application/gzip', 
                                            resumable=True,
                                            )
            request = self.drive.files().create(
                                body=body,
                                media_body=media_body,
                                )
            try: 
                response = None
                while response is None:
                    status, response = request.next_chunk()
            except apiclient.errors.HttpError as e:
              if e.resp.status in [404]:
                logger.error(f'archive_store_folder: 404, {e}') # It should... # Start the upload all over again.
              elif e.resp.status in [500, 502, 503, 504]:
                logger.error(f'archive_store_folder: 5xx, {e}') # It should... # Call next_chunk() again, but use an exponential backoff for repeated errors.
              else:
                logger.error(f'archive_store_folder: {e}') # It should... # Do not retry. Log the error and fail.
        return body['name']
        
    def archive_store_database_media(self):
        # TODO: if apps end up having imagefields, filefields etc.
        # See e.g.
        # https://github.com/nathan-osman/django-archive/blob/master/django_archive/management/commands/archive.py
        print('Not implemented. No database media yet!')
        pass
    
    def archive_store_folder(self, folder_path):
        """
        Archive and store in Google Drive the contents of the folder (recursively)
        Returns name of uploaded file
        """
        folder_path = os.path.normpath(folder_path)
        folder_name = os.path.basename(folder_path)
        with SpooledTemporaryFile() as f:
            # Archive to tar
            with tarfile.open(fileobj=f, mode='x:bz2') as tar:
                tar.add(folder_path)
            # Store in Google Drive
            body = {
                'name': folder_name + backup_suffix() + '.tar.gz',
                }
            media_body = apiclient.http.MediaIoBaseUpload(f, 
                                            mimetype='application/gzip', 
                                            resumable=True,
                                            )
            request = self.drive.files().create(
                                body=body,
                                media_body=media_body,
                                )
            try: 
                response = None
                while response is None:
                    status, response = request.next_chunk()
            except apiclient.errors.HttpError as e:
              if e.resp.status in [404]:
                logger.error(f'archive_store_folder: 404, {e}') # It should... # Start the upload all over again.
              elif e.resp.status in [500, 502, 503, 504]:
                logger.error(f'archive_store_folder: 5xx, {e}') # It should... # Call next_chunk() again, but use an exponential backoff for repeated errors.
              else:
                logger.error(f'archive_store_folder: {e}') # It should... # Do not retry. Log the error and fail.
        return body['name']

    def list_stored_files(self):
        """
        Utility function, typically for interactive use
        """
        print('Listing all stored files')
        drive_list = self.drive.files().list().execute()
        for meta in drive_list['files']:
            print(self.drive.files().get(fileId=meta['id'], fields='name,size,createdTime').execute())
    
    def download_file(self, file_id, file_path):
        """
        Utility function, typically for interactive use
        """
        request = self.drive.files().get_media(fileId=file_id)
        with open(file_path, 'wb') as f:
            downloader = apiclient.http.MediaIoBaseDownload(f, request)
            try:
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                print(f'Downloaded {file_path}')
            except apiclient.errors.HttpError as e:
              if e.resp.status in [404]:
                print('Error: 404') # It should... # Start the upload all over again.
              elif e.resp.status in [500, 502, 503, 504]:
                print('Error: 5xx') # It should... # Call next_chunk() again, but use an exponential backoff for repeated errors.
              else:
                print('Error') # It should... # Do not retry. Log the error and fail.
    
    def download_file_named(self, filename):
        """
        Utility function, typically for interactive use
        """
        query = f"name='{filename}'"
        drive_list = self.drive.files().list(q=query).execute()
        try:
           file_id = drive_list['files'][0]['id']
        except:
            print('Could not find {filename}')
            raise ValueError
        self.download_file(file_id, filename)
    
    
    def delete_file(self, file_id):
        """
        Utility function, typically for interactive use
        """
        self.drive.files().delete(fileId=file_id).execute()
    
    def delete_file_named(self, filename):
        """
        Utility function, typically for interactive use
        """
        query = f"name='{filename}'"
        drive_list = self.drive.files().list(q=query).execute()
        try:
           file_id = drive_list['files'][0]['id']
        except:
            print('Could not find {filename}')
            raise ValueError
        print(f"Deleting {drive_list['files'][0]['name']}")
        self.delete_file(file_id)
        
    def delete_all(self):
        """
        Utility function, typically for interactive use
        """
        drive_list = self.drive.files().list().execute()
        for meta in drive_list['files']:
            print(f"Deleting {meta['name']}...")
            self.drive.files().delete(fileId=meta['id']).execute()

if __name__ == '__main__':
    backup = Command()
    backup.list_stored_files()
