from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render


@login_required
def debug(request, *args, **kwargs):
    user = request.user
    if user.is_staff or user.is_superuser:
        return render(request, 'realtime_debug.html')
    raise Http404
