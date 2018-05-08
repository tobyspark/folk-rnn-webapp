import pytest

from backup.management.commands.backup import Command

def test_upload():
    backup = Command()
    uploaded_name = backup.archive_store_folder(__file__) # will store individual file as well as a folder recursively
    backup.delete_file_named(uploaded_name)
    