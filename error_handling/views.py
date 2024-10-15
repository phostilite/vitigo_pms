# error_handling/views.py

from django.shortcuts import render

def handler400(request, exception):
    return render(request, 'error_handling/400.html', status=400)

def handler403(request, exception):
    return render(request, 'error_handling/403.html', status=403)

def handler404(request, exception):
    return render(request, 'error_handling/404.html', status=404)

def handler500(request):
    return render(request, 'error_handling/500.html', status=500)