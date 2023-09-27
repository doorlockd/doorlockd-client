from django.forms import ModelForm
from .models import Lock, Key, Person, SyncLockKeys, LogUnknownKey


class PersonForm(ModelForm):
    class Meta:
        model = Person
        fields = ['id', 'name', 'email', 'info', 'is_enabled']
        # add keys

class KeyForm(ModelForm):
    class Meta:
        model = Key
        fields = ['hwid','description','is_enabled', 'owner']
        # logkeylastseen fields ??

class LogUnknownKeyForm(ModelForm):
    class Meta:
        model = LogUnknownKey
        fields = ['hwid', 'counter', 'lock']
        # 'created_at', 'updated_at', 'last_seen',

class LockForm(ModelForm):
    class Meta:
        model = Lock
        fields = ['name', 'description', 'certificate', 'is_enabled']
