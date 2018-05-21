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
from django.conf.urls import url
from composer import views

urlpatterns = [
    url(r'^$', views.home_page, name='home'),
    url(r'^tune/$', views.tune_page, name='tune'),
    url(r'^tune/(?P<tune_id>[0-9]+)$', views.tune_page, name='tune'),
    url(r'^tune/(?P<tune_id>[0-9]+)/archive$', views.archive_tune, name='archive_tune'),
    url(r'^competition/$', views.competition_page, name='competition')
]
