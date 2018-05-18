"""folk_rnn_site URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.views.generic import RedirectView
from django.contrib import admin
from archiver import views

urlpatterns = [
    url(r'^$', views.home_page, name='home'),
    url(r'^tune/$', RedirectView.as_view(url='/tunes', permanent=True)),
    url(r'^tunes/$', views.tunes_page, name='tunes'),
    url(r'^tune/(?P<tune_id>[0-9]+)$', views.tune_page, name='tune'),
    url(r'^tune/(?P<tune_id>[0-9]+)/download$', views.tune_download, name='tune_download'),
    url(r'^tune/(?P<tune_id>[0-9]+)/download/setting/(?P<setting_id>[0-9]+)$', views.setting_download, name='setting_download'),
    url(r'^tune/(?P<tune_id>[0-9]+)/download/all$', views.tune_setting_download, name='tune_setting_download'),
    url(r'^recordings/$', views.recordings_page, name='recordings'),
    url(r'^recording/(?P<recording_id>[0-9]+)$', views.recording_page, name='recording'),
    url(r'^events/$', views.events_page, name='events'),
    url(r'^event/(?P<event_id>[0-9]+)$', views.event_page, name='event'),
    url(r'^submit/$', views.submit_page, name='submit'),
    url(r'^questions/$', views.questions_page, name='questions'),
    url(r'^dataset$', views.dataset_download),
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^signup', views.signup, name='signup'),
    url(r'^admin/', admin.site.urls),
]
