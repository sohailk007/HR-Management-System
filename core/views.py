from django.shortcuts import render

def home_view(request):
    """
    Public home page view.
    """
    return render(request, 'index.html')