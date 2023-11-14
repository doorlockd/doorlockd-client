from faulthandler import is_enabled
from os import access
from re import L
from xml.dom import ValidationErr
from django.test import TestCase
from django.utils import timezone

from .models import Person, Key, UnknownKey, Lock
from django.core.exceptions import ValidationError

from  . import factory


# todo:
# - randomkey data integrity (#case we need to clean up saved keys from RandomKeyTestCase)

class RandomKeyTestCase(TestCase):
    """
    Can create non-uniqe keys using random hardware identifiers (^08:.... ) 
    """
    def test_always_good(self):
        # just learning tests
        self.assertIs(False, False)

    # # uncommented : we do not validate UnknownKey, up to the lock. 
    # def test_validate_random_hwid_unknownkey(self):
    #     l = Lock(name='test lock')
    #     l.save()

    #     with self.assertRaises(ValidationError):
    #         k = UnknownKey(hwid="08:00:00:00", lock=l)
    #         k.save()



    def test_validate_random_hwid(self):
        # p = Person(name='test user')
        p = factory.RandomPerson()
        print(p)
        p.save()

        # self.assertRaises(ValidationError, k.save())
        with self.assertRaises(ValidationError):
            k = Key(hwid="08:00:00:00", owner=p)
            k.save()

    def test_factory_data(self):
        p = factory.RandomPerson()
        print(p)


from django.test import Client

class ViewTests(TestCase):
    def setUp(self):
        # Every test needs a client.
        self.client = Client()
        
        # make bunch of models:
        self.m = {}

        # scenario matrix:
        #
        # Lock.is_enabled [True, False]
        # Access [ Yes , No ]
        # Key.is_enabled [True,False]
        # Person.is_enabled [True,False]

        # Lock Enabled + Disabled:
        self.m['lock_enabled'] = factory.RandomLock.create(is_enabled=True) 
        self.m['lock_disabled'] = factory.RandomLock.create(is_enabled=False)

        # Person Enabled + Disabled:
        self.m['person_enabled'] = factory.RandomPerson.create(is_enabled=True) 
        self.m['person_enabled'].access.add(self.m['lock_enabled'])
        self.m['person_enabled'].access.add(self.m['lock_disabled'])

        self.m['person_disabled'] = factory.RandomPerson.create(is_enabled=False)
        self.m['person_disabled'].access.add(self.m['lock_enabled'])
        self.m['person_disabled'].access.add(self.m['lock_disabled'])


        # Key Enabled + Disabled for both persons:
        self.m['key_enabled_person_enabled'] = factory.RandomKey.create(is_enabled=True, owner=self.m['person_enabled'])
        self.m['key_disabled_person_enabled'] = factory.RandomKey.create(is_enabled=False, owner=self.m['person_enabled'])
        self.m['key_enabled_person_disabled'] = factory.RandomKey.create(is_enabled=True, owner=self.m['person_disabled'])
        self.m['key_disabled_person_disabled'] = factory.RandomKey.create(is_enabled=False, owner=self.m['person_disabled'])

        # 
        # Lock Enabled + Disabled NO ACCESS:
        self.m['lock_enabled_noaccess'] = factory.RandomLock.create(is_enabled=True)
        self.m['lock_disabled_noaccess'] = factory.RandomLock.create(is_enabled=False)
        # Person Enabled + Disabled NO ACCESS:
        self.m['person_enabled_noaccess'] = factory.RandomPerson.create(is_enabled=True)
        self.m['person_disabled_noaccess'] = factory.RandomPerson.create(is_enabled=False)
        # Key Enabled + Disabled for both persons:
        self.m['key_enabled_person_enabled_noaccess'] = factory.RandomKey.create(is_enabled=True, owner=self.m['person_enabled_noaccess'])
        self.m['key_disabled_person_enabled_noaccess'] = factory.RandomKey.create(is_enabled=False, owner=self.m['person_enabled_noaccess'])
        self.m['key_enabled_person_disabled_noaccess'] = factory.RandomKey.create(is_enabled=True, owner=self.m['person_disabled_noaccess'])
        self.m['key_disabled_person_disabled_noaccess'] = factory.RandomKey.create(is_enabled=False, owner=self.m['person_disabled_noaccess'])


        # print(self.m)
        # for fun add random data:
        # factory.seed_db(add_locks=[ self.m['lock_enabled'], self.m['lock_disabled'] ])

    def test_first_view_test(self):
        # get lock + key from our pre made objects:
        l = self.m['lock_enabled']
        k = self.m['key_enabled_person_enabled']

        response = self.client.get(f'/doorlockdb/{l.name}/keys')
        # print('Response:', response)
        # print('Response.content:', response.content)
        # print('response.context:', response.context)

        self.assertNotContains(response, k.hwid, status_code=403) 

    def test_lock_sync_no_passsword(self):
        # get lock + key from our pre made objects:
        l = self.m['lock_enabled']
        k = self.m['key_enabled_person_enabled']

        response = self.client.get(f'/doorlockdb/{l.name}/keys')

        # should not show hwid of enabled key:
        self.assertNotContains(response, k.hwid, status_code=403) 

    def test_lock_sync_ok(self):
        # get lock + key from our pre made objects:
        l = self.m['lock_enabled']
        k = self.m['key_enabled_person_enabled']

        # query:
        response = self.client.post(f'/doorlockdb/{l.name}/keys', {'secret': l.secret})


        # should show hwid of enabled key:
        self.assertIn(self.m['key_enabled_person_enabled'].hwid, response.json()['keys'] )
        # should not show any of the other keys:
        self.assertNotIn(self.m['key_disabled_person_enabled'].hwid, response.json()['keys'])
        self.assertNotIn(self.m['key_disabled_person_disabled'].hwid, response.json()['keys'])
        self.assertNotIn(self.m['key_enabled_person_enabled_noaccess'].hwid, response.json()['keys'])
        self.assertNotIn(self.m['key_disabled_person_enabled_noaccess'].hwid, response.json()['keys'])
        self.assertNotIn(self.m['key_disabled_person_disabled_noaccess'].hwid, response.json()['keys'])
        self.assertNotIn(self.m['key_enabled_person_disabled_noaccess'].hwid, response.json()['keys'])

        # print('Response:', response)
        # print('Response.content:', response.content)
        # print('response.context:', response.context)
        # print('test: response.json()[keys]:', response.json()['keys'])

    def test_lock_disabled_sync_error(self):
        # lock disabled:
        # expect: empty response (no person will have access)
        # get lock + key from our pre made objects:
        l = self.m['lock_disabled']
        
        # query:
        response = self.client.post(f'/doorlockdb/{l.name}/keys', {'secret': l.secret})

        # should not show any hwid of enabled key:
        self.assertEqual([], response.json()['keys']) # empty keys list

        # double check for any 'hwid' leaking in the response:
        self.assertNotContains(response, self.m['key_enabled_person_enabled'].hwid)
        self.assertNotContains(response, self.m['key_disabled_person_enabled'].hwid)
        self.assertNotContains(response, self.m['key_disabled_person_disabled'].hwid)
        self.assertNotContains(response, self.m['key_enabled_person_disabled'].hwid)
        self.assertNotContains(response, self.m['key_enabled_person_enabled_noaccess'].hwid)
        self.assertNotContains(response, self.m['key_disabled_person_enabled_noaccess'].hwid)
        self.assertNotContains(response, self.m['key_disabled_person_disabled_noaccess'].hwid)
        self.assertNotContains(response, self.m['key_enabled_person_disabled_noaccess'].hwid)

        # print('Response.content:', response.content)

    def test_lock_sync_wrong_password(self):
        pass 