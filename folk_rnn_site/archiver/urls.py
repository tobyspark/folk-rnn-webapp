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
from django_registration.backends.activation.views import RegistrationView
from django.contrib import admin
from archiver import views, forms

urlpatterns = [
    url(r'^$', views.home_page, name='home'),
    url(r'^tune/$', RedirectView.as_view(url='/tunes', permanent=True)),
    url(r'^tunes/$', views.tunes_page, name='tunes'),
    url(r'^tune/(?P<tune_id>\d+)$', views.tune_page, name='tune'),
    url(r'^tune/(?P<tune_id>\d+)/setting/(?P<setting_id>\d+)$', views.setting_redirect, name='setting'),
    url(r'^tune/(?P<tune_id>\d+)/download$', views.tune_download, name='tune_download'),
    url(r'^tune/(?P<tune_id>\d+)/download/setting/(?P<setting_id>\d+)$', views.setting_download, name='setting_download'),
    url(r'^tune/(?P<tune_id>\d+)/download/all$', views.tune_setting_download, name='tune_setting_download'),
    url(r'^recording/$', RedirectView.as_view(url='/recordings', permanent=True)),
    url(r'^recordings/$', views.recordings_page, name='recordings'),
    url(r'^recording/(?P<recording_id>\d+)$', views.recording_page, name='recording'),
    url(r'^event/$', RedirectView.as_view(url='/events', permanent=True)),
    url(r'^events/$', views.events_page, name='events'),
    url(r'^event/(?P<event_id>\d+)$', views.event_page, name='event'),
    url(r'^member/(?P<user_id>\d+)$', views.user_page, name='user'),
    url(r'^member/(?P<user_id>\d+)/tunebook$', views.tunebook_page, name='tunebook'),
    url(r'^member/(?P<user_id>\d+)/tunebook/download$', views.tunebook_download, name='tunebook_download'),
    url(r'^tune-of-the-month/$', views.competitions_page, name='competitions'),
    url(r'^tune-of-the-month/(?P<competition_id>\d+)$', views.competition_page, name='competition'),
    url(r'^submit/$', views.submit_page, name='submit'),
    url(r'^questions/$', views.questions_page, name='questions'),
    url(r'^help/$', views.help_page, name='help'),
    url(r'^dataset$', views.dataset_download),
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^register/$',
     RegistrationView.as_view(form_class=forms.RegistrationForm),
     name='django_registration_register',
     ),
    url(r'^', include('django_registration.backends.activation.urls')),
    url(r'^admin/', admin.site.urls),
]
