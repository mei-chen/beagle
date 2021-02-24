from rest_framework.generics import GenericAPIView
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated

from portal.api.serializers import ProfileSerialzer
from portal.models import Profile


class ProfileAPI(RetrieveModelMixin,
                 UpdateModelMixin,
                 GenericAPIView):
    """
    Direct access to the current user's profile via /api/v1/profile/.
    Allowed methods: GET, PUT, PATCH.
    """

    serializer_class = ProfileSerialzer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        user = self.request.user
        profile, _ = Profile.objects.get_or_create(user=user)
        return profile

    def get(self, request, *args, **kwargs):
        return super(ProfileAPI, self).retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return super(ProfileAPI, self).update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return super(ProfileAPI, self).partial_update(request, *args, **kwargs)
