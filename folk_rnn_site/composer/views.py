from django.shortcuts import redirect, render

from composer.models import Tune

def composer_page(request):
    if request.method == 'POST':
        Tune.objects.create(seed=request.POST['seed_text'])
        return redirect('/')
        
    return render(request, 'compose.html')

