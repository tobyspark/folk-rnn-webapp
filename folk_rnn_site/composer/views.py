from django.shortcuts import render

def composer_page(request):
    if request.method == 'POST':
        return render(request, 'compose.html', {
            'seed_text': request.POST['seed_text'],
        })
    return render(request, 'compose.html')
