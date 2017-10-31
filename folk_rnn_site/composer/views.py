from django.shortcuts import render
from django.http import HttpResponse

def composer_page(request):
    return HttpResponse('<html><title>Folk_RNN Composer</title></html>')
