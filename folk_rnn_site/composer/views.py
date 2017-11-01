from django.shortcuts import render

def composer_page(request):
    return render(request, 'compose.html')
