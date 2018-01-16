import os
import channels.asgi

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'folk_rnn_site.settings')

channel_layer = channels.asgi.get_channel_layer()
