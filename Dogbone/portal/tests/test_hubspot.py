import mock
import json
from dogbone.testing.base import BeagleWebTest
from portal.tasks import hubspot_submit_form, hubspot_update_contact_properties, hubspot_get_vid
from django.conf import settings


class HubSpotTest(BeagleWebTest):
    def test_hubspot_register_form_submit(self):
        with mock.patch('integrations.hubspot.Request') as MockRequest:
            with mock.patch('integrations.hubspot.Session.send') as mock_send:
                type(mock_send.return_value).status_code = mock.PropertyMock(return_value=204)
                result = hubspot_submit_form(settings.HUBSPOT_REGISTER_FORM_GUID,
                                             url='/some/url',
                                             ip='61.62.63.64',
                                             hutk=None,
                                             page_name='RegisterForm',
                                             data={'coupon_code': 'COUPON',
                                                   'username': self.user.username,
                                                   'lifecyclestage': 'lead',
                                                   'email': self.user.email,
                                                   'hs_lead_status': 'UNQUALIFIED',
                                                   'blog_default_hubspot_blog_subscription': 'weekly',})
                MockRequest.assert_called_once_with('POST',
                                                    'https://forms.hubspot.com/uploads/form/v2/541681/%s' % settings.HUBSPOT_REGISTER_FORM_GUID,
                                                    data={'username': self.user.username,
                                                          'lifecyclestage': 'lead',
                                                          'coupon_code': 'COUPON',
                                                          'email': self.user.email,
                                                          'blog_default_hubspot_blog_subscription': 'weekly',
                                                          'hs_lead_status': 'UNQUALIFIED',
                                                          'hs_context': json.dumps({"pageName": "RegisterForm",
                                                                                    "pageUrl": "/some/url",
                                                                                    "ipAddress": "61.62.63.64"})}
                )

                self.assertTrue(result)

    def test_hubspot_register_form_submit_400(self):
        with mock.patch('integrations.hubspot.Request') as MockRequest:
            with mock.patch('integrations.hubspot.Session.send') as mock_send:
                type(mock_send.return_value).status_code = mock.PropertyMock(return_value=400)
                result = hubspot_submit_form(settings.HUBSPOT_REGISTER_FORM_GUID,
                                             url='/some/url',
                                             ip='61.62.63.64',
                                             hutk=None,
                                             page_name='RegisterForm',
                                             data={'coupon_code': 'COUPON',
                                                   'username': self.user.username,
                                                   'lifecyclestage': 'lead',
                                                   'email': self.user.email,
                                                   'hs_lead_status': 'UNQUALIFIED',
                                                   'blog_default_hubspot_blog_subscription': 'weekly',})

                MockRequest.assert_called_once_with('POST',
                                                    'https://forms.hubspot.com/uploads/form/v2/541681/%s' % settings.HUBSPOT_REGISTER_FORM_GUID,
                                                    data={'username': self.user.username,
                                                          'lifecyclestage': 'lead',
                                                          'coupon_code': 'COUPON',
                                                          'email': self.user.email,
                                                          'blog_default_hubspot_blog_subscription': 'weekly',
                                                          'hs_lead_status': 'UNQUALIFIED',
                                                          'hs_context': json.dumps({"pageName": "RegisterForm",
                                                                                    "pageUrl": "/some/url",
                                                                                    "ipAddress": "61.62.63.64"})}
                )
                self.assertFalse(result)

    def test_hubspot_external_register_form_submit(self):
        other_user = self.create_user('email@gmail.com', 'funkyfresh', '12344321')
        with mock.patch('integrations.hubspot.Request') as MockRequest:
            with mock.patch('integrations.hubspot.Session.send') as mock_send:
                type(mock_send.return_value).status_code = mock.PropertyMock(return_value=204)
                result = hubspot_submit_form(settings.HUBSPOT_EXTERNAL_REGISTER_FORM_GUID,
                                             url='/some/url',
                                             ip='61.62.63.64',
                                             hutk=None,
                                             page_name='ExternalRegisterForm',
                                             data={'invited_by': other_user.email,
                                                   'username': self.user.username,
                                                   'lifecyclestage': 'lead',
                                                   'email': self.user.email,
                                                   'hs_lead_status': 'UNQUALIFIED',
                                                   'blog_default_hubspot_blog_subscription': 'weekly'})
                MockRequest.assert_called_once_with('POST',
                                                    'https://forms.hubspot.com/uploads/form/v2/541681/%s' % settings.HUBSPOT_EXTERNAL_REGISTER_FORM_GUID,
                                                    data={'username': self.user.username,
                                                          'lifecyclestage': 'lead',
                                                          'email': self.user.email,
                                                          'blog_default_hubspot_blog_subscription': 'weekly',
                                                          'hs_lead_status': 'UNQUALIFIED',
                                                          'invited_by': other_user.email,
                                                          'hs_context': json.dumps({"pageName": "ExternalRegisterForm",
                                                                                    "pageUrl": "/some/url",
                                                                                    "ipAddress": "61.62.63.64"})}
                )

                self.assertTrue(result)

    def test_hubspot_external_register_form_submit_400(self):
        other_user = self.create_user('email@gmail.com', 'funkyfresh', '12344321')
        with mock.patch('integrations.hubspot.Request') as MockRequest:
            with mock.patch('integrations.hubspot.Session.send') as mock_send:
                type(mock_send.return_value).status_code = mock.PropertyMock(return_value=400)
                result = hubspot_submit_form(settings.HUBSPOT_EXTERNAL_REGISTER_FORM_GUID,
                                             url='/some/url',
                                             ip='61.62.63.64',
                                             hutk=None,
                                             page_name='ExternalRegisterForm',
                                             data={'invited_by': other_user.email,
                                                   'username': self.user.username,
                                                   'lifecyclestage': 'lead',
                                                   'email': self.user.email,
                                                   'hs_lead_status': 'UNQUALIFIED',
                                                   'blog_default_hubspot_blog_subscription': 'weekly'})
                MockRequest.assert_called_once_with('POST',
                                                    'https://forms.hubspot.com/uploads/form/v2/541681/%s' % settings.HUBSPOT_EXTERNAL_REGISTER_FORM_GUID,
                                                    data={'username': self.user.username,
                                                          'lifecyclestage': 'lead',
                                                          'email': self.user.email,
                                                          'blog_default_hubspot_blog_subscription': 'weekly',
                                                          'hs_lead_status': 'UNQUALIFIED',
                                                          'invited_by': other_user.email,
                                                          'hs_context': json.dumps({"pageName": "ExternalRegisterForm",
                                                                                    "pageUrl": "/some/url",
                                                                                    "ipAddress": "61.62.63.64"})}
                )
                self.assertFalse(result)

    def test_hubspot_get_vid(self):
        with mock.patch('integrations.hubspot.Request') as MockRequest:
            with mock.patch('integrations.hubspot.Session.send') as mock_send:
                type(mock_send.return_value).status_code = mock.PropertyMock(return_value=200)
                type(mock_send.return_value).content = json.dumps({ "vid":1234,
                                                                    "canonical-vid":1234,
                                                                    "merged-vids":[],
                                                                    "portal-id":541681,
                                                                    "is-contact":True,
                                                                    "profile-token":"AO_T-mPp9rnrEs6CrLVdY6FvTG1A4yd8t4lICspPU3Trnnsx-ARzEOoXWNiYangcNm9Oe3YbZjBt7fw84rbWMEY8RTtu017OT-Rd2RTMqpf3XrnNw92V42MlYnyUa79Do5rA5Tb_gPTv",
                                                                    "profile-url":"https://app.hubspot.com/contacts/541681/lists/public/contact/_AO_T-mPp9rnrEs6CrLVdY6FvTG1A4yd8t4lICspPU3Trnnsx-ARzEOoXWNiYangcNm9Oe3YbZjBt7fw84rbWMEY8RTtu017OT-Rd2RTMqpf3XrnNw92V42MlYnyUa79Do5rA5Tb_gPTv/",
                                                                    "properties":{},
                                                                    "identity-profiles":
                                                                        [
                                                                            {
                                                                                "vid":1234,
                                                                                "saved-at-timestamp":1438234449208,
                                                                                "deleted-changed-timestamp":0,
                                                                                "identities":[
                                                                                    {
                                                                                        "type":"EMAIL",
                                                                                        "value":"henry@sniffthefineprint.com",
                                                                                        "timestamp":1438234449183
                                                                                    },
                                                                                    {
                                                                                        "type":"LEAD_GUID",
                                                                                        "value":"7b625c5d-816b-4604-a33d-7d02fe5b7ef8",
                                                                                        "timestamp":1438234449204
                                                                                    }
                                                                                ]
                                                                            }
                                                                        ],
                                                                    "merge-audits":[]
                })
                result = hubspot_get_vid(email=self.user.email)


                MockRequest.assert_called_once_with('GET',
                                                    'https://api.hubapi.com/contacts/v1/contact/email/%s/profile?hapikey=%s&property=vid&formSubmissionMode=none&showListMemberships=false' % (self.user.email, settings.HUBSPOT_API_KEY))
                self.assertEqual(result, 1234)

    def test_hubspot_get_vid_404(self):
        with mock.patch('integrations.hubspot.Request') as MockRequest:
            with mock.patch('integrations.hubspot.Session.send') as mock_send:
                type(mock_send.return_value).status_code = mock.PropertyMock(return_value=404)
                type(mock_send.return_value).content = json.dumps({ "vid":1234,
                                                                    "canonical-vid":1234,
                                                                    "merged-vids":[],
                                                                    "portal-id":541681,
                                                                    "is-contact":True,
                                                                    "profile-token":"AO_T-mPp9rnrEs6CrLVdY6FvTG1A4yd8t4lICspPU3Trnnsx-ARzEOoXWNiYangcNm9Oe3YbZjBt7fw84rbWMEY8RTtu017OT-Rd2RTMqpf3XrnNw92V42MlYnyUa79Do5rA5Tb_gPTv",
                                                                    "profile-url":"https://app.hubspot.com/contacts/541681/lists/public/contact/_AO_T-mPp9rnrEs6CrLVdY6FvTG1A4yd8t4lICspPU3Trnnsx-ARzEOoXWNiYangcNm9Oe3YbZjBt7fw84rbWMEY8RTtu017OT-Rd2RTMqpf3XrnNw92V42MlYnyUa79Do5rA5Tb_gPTv/",
                                                                    "properties":{},
                                                                    "identity-profiles":
                                                                        [
                                                                            {
                                                                                "vid":1234,
                                                                                "saved-at-timestamp":1438234449208,
                                                                                "deleted-changed-timestamp":0,
                                                                                "identities":[
                                                                                    {
                                                                                        "type":"EMAIL",
                                                                                        "value":"henry@sniffthefineprint.com",
                                                                                        "timestamp":1438234449183
                                                                                    },
                                                                                    {
                                                                                        "type":"LEAD_GUID",
                                                                                        "value":"7b625c5d-816b-4604-a33d-7d02fe5b7ef8",
                                                                                        "timestamp":1438234449204
                                                                                    }
                                                                                ]
                                                                            }
                                                                        ],
                                                                    "merge-audits":[]
                })
                result = hubspot_get_vid(email=self.user.email)


                MockRequest.assert_called_once_with('GET',
                                                    'https://api.hubapi.com/contacts/v1/contact/email/%s/profile?hapikey=%s&property=vid&formSubmissionMode=none&showListMemberships=false' % (self.user.email, settings.HUBSPOT_API_KEY))
                self.assertFalse(result)


    def test_hubspot_update_contact_properties(self):
        with mock.patch('integrations.hubspot.Request') as MockRequest:
            with mock.patch('integrations.hubspot.Session.send') as mock_send:
                with mock.patch('portal.tasks.hubspot_get_vid', return_value=1234) as mock_get_vid:
                    type(mock_send.return_value).status_code = mock.PropertyMock(return_value=204)

                    result = hubspot_update_contact_properties(email="new-email@hubspot.com",
                                                               data=[
                                                                   {
                                                                       "property": "email",
                                                                       "value": "new-email@hubspot.com"
                                                                   },
                                                                   {
                                                                       "property": "firstname",
                                                                       "value": "Hank",
                                                                       "timestamp": 1419284759000,
                                                                       }
                                                               ])
                    MockRequest.assert_called_once_with('POST',
                                                        'https://api.hubapi.com/contacts/v1/contact/vid/%s/profile?hapikey=%s' % (1234, settings.HUBSPOT_API_KEY),
                                                        data=json.dumps({'properties': [
                                                            {
                                                                "property": "email",
                                                                "value": "new-email@hubspot.com"
                                                            },
                                                            {
                                                                "property": "firstname",
                                                                "value": "Hank",
                                                                "timestamp": 1419284759000,
                                                                }
                                                        ] }))
                    self.assertTrue(result)
                    mock_get_vid.assert_called_with('new-email@hubspot.com')

    def test_hubspot_update_contact_properties_400(self):
        with mock.patch('integrations.hubspot.Request') as MockRequest:
            with mock.patch('integrations.hubspot.Session.send') as mock_send:
                with mock.patch('portal.tasks.hubspot_get_vid', return_value=1234) as mock_get_vid:
                    type(mock_send.return_value).status_code = mock.PropertyMock(return_value=400)

                    result = hubspot_update_contact_properties(email='new-email@hubspot.com',
                                                               data=[
                                                                   {
                                                                       "property": "email",
                                                                       "value": "new-email@hubspot.com"
                                                                   },
                                                                   {
                                                                       "property": "firstname",
                                                                       "value": "Hank",
                                                                       "timestamp": 1419284759000,
                                                                       }
                                                               ])
                    MockRequest.assert_called_once_with('POST',
                                                        'https://api.hubapi.com/contacts/v1/contact/vid/%s/profile?hapikey=%s' % (1234, settings.HUBSPOT_API_KEY),
                                                        data=json.dumps({'properties': [
                                                            {
                                                                "property": "email",
                                                                "value": "new-email@hubspot.com"
                                                            },
                                                            {
                                                                "property": "firstname",
                                                                "value": "Hank",
                                                                "timestamp": 1419284759000,
                                                                }
                                                        ] }))
                    self.assertFalse(result)

                    mock_get_vid.assert_called_with('new-email@hubspot.com')

