"""Views for the pages app."""
from django.shortcuts import render
from django.views.decorators.http import require_GET

@require_GET
def home(request):
    """Render the marketing landing page."""
    return render(request, "pages/index.html")