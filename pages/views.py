"""Views for the pages app."""
from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET


@require_GET
def home(request):
    """Render the marketing landing page."""
    # If user is already logged in, redirect to menu
    if request.user.is_authenticated:
        return redirect('menu:catalog')
    
    return render(request, "pages/index.html")