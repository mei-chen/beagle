from django.core.urlresolvers import reverse
from dogbone.testing.base import BeagleWebTest
from authentication.models import OneTimeLoginHash
from django.contrib.auth import authenticate


class OneTimeLoginHashTest(BeagleWebTest):
    def test_create_hash(self):
        onetime_hash_model = OneTimeLoginHash.create(self.user)
        serialized_hash = onetime_hash_model.get_hash()
        self.assertEqual(OneTimeLoginHash.get_onetime_model(serialized_hash), onetime_hash_model)

    def test_resolved_hash(self):
        onetime_hash_model = OneTimeLoginHash.create(self.user)
        onetime_hash_model.resolve()
        serialized_hash = onetime_hash_model.get_hash()
        self.assertEqual(OneTimeLoginHash.get_onetime_model(serialized_hash), None)

    def test_authentication(self):
        onetime_hash_model = OneTimeLoginHash.create(self.user)
        u = authenticate(login_hash=onetime_hash_model.get_hash())
        self.assertEqual(self.user, u)

        u = authenticate(login_hash=onetime_hash_model.get_hash())
        self.assertEqual(u, None)


