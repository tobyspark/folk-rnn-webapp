"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
As per https://channels.readthedocs.io/en/latest/deploying.html
"""

import os
import django
from channels.routing import get_default_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'folk_rnn_site.settings')
django.setup()
application = get_default_application()
