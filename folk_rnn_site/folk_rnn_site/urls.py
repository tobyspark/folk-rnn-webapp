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
from composer import views as c_views
from archiver import views as a_views

urlpatterns = [
    # FIXME, composer host
    url(r'^$', c_views.home_page, name='home'),
    url(r'^tune/$', c_views.tune_page, name='tune'),
    url(r'^tune/(?P<tune_id>[0-9]+)$', c_views.tune_page, name='tune'),
    # FIXME, archive host
    url(r'^archive/$', a_views.home_page, name='home'),
    url(r'^archive/tune/$', a_views.tune_page, name='tune'),
    url(r'^archive/tune/(?P<tune_id>[0-9]+)$', a_views.tune_page, name='tune'),
    url(r'^archive/tune/new', a_views.new_tune),
    url(r'^archive/dataset$', a_views.dataset_download),
]
