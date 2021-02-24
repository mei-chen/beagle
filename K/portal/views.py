from uuid import uuid4

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from rest_framework.views import APIView

from core.utils import user_to_dict
from portal.tasks import gather_personal_data_from_text


@login_required(login_url='/accounts/login/')
def index(request):
    context = {
        'HOT_LOAD': settings.HOT_LOAD,
        'MAX_UPLOAD_SIZE': settings.DATA_UPLOAD_MAX_MEMORY_SIZE,
        'DROPBOX_APP_KEY': settings.DROPBOX_APP_KEY
    }
    return render(request, 'portal/index.html', context)


class UserDetails(APIView):

    def get(self, request):
        return JsonResponse(user_to_dict(request.user))


class FindPersonalData(APIView):

    def post(self, request):
        text = request.data['text']
        callback_url = request.data['callback_url']
        id = request.data['id']
        uuid = uuid4()
        gather_personal_data_from_text.delay(text, callback_url, id, uuid)

        return HttpResponse(uuid)
