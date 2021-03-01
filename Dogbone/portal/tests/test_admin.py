# -*- coding: utf-8 -*-

from dogbone.testing.base import BeagleWebTest
from core.models import ExternalInvite


class AdminTest(BeagleWebTest):
    NEED_DEFAULT_USER = False

    def setUp(self):
        super(AdminTest, self).setUp()
        self.user = self.create_user()

    def test_external_invite_url(self):
        """ Check that the url actually exists """

        response = self.client.get('/adm/office/core/externalinvite/')
        self.assertEqual(response.status_code, 200)

    def test_unicode_external_invite_name(self):
        d = self.create_document(title=u'abcdé', owner=self.user, pending=False)

        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()

        self.login()

        ExternalInvite.objects.create(email='aaa@ggg.com', document=d, inviter=self.user)

        response = self.client.get('/adm/office/core/externalinvite/')
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, u'abcdé')
