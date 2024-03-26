from django import forms
from django.contrib.auth.decorators import permission_required
# from django.contrib.auth.models import Group
from django.db import transaction
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic.edit import FormView

from .models import Person, PersonGroup


@method_decorator(permission_required('auth.change_group'), name='dispatch')
class AddUsersToGroupView(FormView):
    model = Person
    admin_site = None  # Filled by __init__
    template_name = 'admin_person_group_bulkaction.html'

    class SelectGroupForm(forms.Form):
        persongroup = forms.ModelChoiceField(
            queryset=PersonGroup.objects.all(),
            label="Add/remove users to/from this group",
        )
    form_class = SelectGroupForm

    def __init__(self, admin_site):
        self.admin_site = admin_site


    def get_context_data(self, **kwargs):
        kwargs.update(self.admin_site.each_context(self.request))
        kwargs.update({
            'opts': self.model._meta,
            'users': Person.objects.filter(pk__in=self.get_userids()),
            'is_add': self.is_add(),
            'is_remove': self.is_remove(),
        })

        # alter form label:
        if self.is_remove():
            self.form_class.base_fields['persongroup'].label = 'Remove users from this group'
        if self.is_add():
            self.form_class.base_fields['persongroup'].label = 'Add users to this group'

        return super().get_context_data(**kwargs)

    def is_add(self):
        return self.kwargs['add_or_remove'] == 'add'

    def is_remove(self):
        return self.kwargs['add_or_remove'] == 'remove'

    def get_userids(self):
        return map(int, self.kwargs['userids'].split(','))

    def form_valid(self, form):
        with transaction.atomic():
            persongroup = form.cleaned_data['persongroup']
            if self.is_add():
                persongroup.persons.add(*self.get_userids())
            if self.is_remove():
                persongroup.persons.remove(*self.get_userids())

        return redirect('admin:doorlockdb_persongroup_change', persongroup.pk)