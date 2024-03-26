from django.contrib import admin

# Register your models here.
from .models import *

from django.utils.html import format_html
from django.urls import reverse
from django import forms
from django.db.models import Count
from django.forms import Textarea

from django.shortcuts import redirect
from django.urls import path
from .adminviews import AddUsersToGroupView

# admin.site.register(Person)
# admin.site.register(PersonGroup)
# admin.site.register(Key)
# admin.site.register(Lock)
# admin.site.register(AccessRuleset)
# admin.site.register(AccessRule)
# admin.site.register(AccessGroup)
# admin.site.register(SyncLockKeys)
# admin.site.register(LogUnknownKey)
# admin.site.register(LogKeyLastSeen)


# more advanced adminModels:
# class KeysInline(admin.StackedInline):
class KeysInline(admin.TabularInline):
    model = Key
    max_num = 0
    readonly_fields = ("hwid",)


@admin.action(description="Enable")
def make_is_enabled_true(modeladmin, request, queryset):
    queryset.update(is_enabled=True)


@admin.action(description="Disable ")
def make_is_enabled_false(modeladmin, request, queryset):
    queryset.update(is_enabled=False)


class LockAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "is_enabled")
    actions = (make_is_enabled_true, make_is_enabled_false)

    formfield_overrides = {
        models.TextField: {
            "widget": Textarea(
                attrs={"rows": 20, "cols": 64, "style": "font-family: monospace"}
            )
        },
    }


# class PersonForm(forms.ModelForm):
#     class Meta:
#         model = Person
#         exclude = ["name"]


@admin.action(description="Add person(s) to group")
def add_person_to_group(self, request, queryset):
    userids = queryset.values_list("pk", flat=True)
    return redirect("admin:bulk_person_to_group", ",".join(map(str, userids)), "add")


@admin.action(description="Remove person(s) from group")
def remove_person_from_group(self, request, queryset):
    userids = queryset.values_list("pk", flat=True)
    return redirect("admin:bulk_person_to_group", ",".join(map(str, userids)), "remove")


class PersonAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "is_enabled",
        "key_count",
        "group_count",
        "last_seen_start",
        "last_seen_end",
        "oops",
    )
    list_filter = (
        "is_enabled",
        "personsgroup",
        "personsgroup__access_groups",
        "personsgroup__access_groups__locks",
    )
    filter_horizontal = ("personsgroup",)

    inlines = [KeysInline]
    actions = (
        make_is_enabled_true,
        make_is_enabled_false,
        add_person_to_group,
        remove_person_from_group,
    )

    def get_queryset(self, request):
        queryset = super(PersonAdmin, self).get_queryset(request)
        return queryset.annotate(key_count=Count("key", distinct=True)).annotate(
            group_count=Count("personsgroup", distinct=True)
        )

    def get_urls(self):
        # Prepend new path so it is before the catchall that ModelAdmin adds
        return [
            path(
                "<path:userids>/<add_or_remove>/bulk-to-group/",
                self.admin_site.admin_view(
                    AddUsersToGroupView.as_view(admin_site=self.admin_site)
                ),
                name="bulk_person_to_group",
            ),
        ] + super().get_urls()

    @admin.display(ordering="key_count", description="#keys")
    def key_count(self, obj):
        return obj.key_count

    @admin.display(ordering="group_count", description="#groups")
    def group_count(self, obj):
        return obj.group_count

    @admin.display
    def oops(self, obj):
        return "disabled"
        msg = ""
        result = checkAnyOutOfSync(obj)
        if result:
            msg = "Oops!!"
        return format_html(f'<span title="{result}">{msg}<span>')
        # return checkAnyOutOfSync(obj)


class PersonGroupMemberInline(admin.TabularInline):
    model = Person.personsgroup.through


class PersonGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "is_enabled", "persons_count")
    list_filter = ("is_enabled",)
    filter_horizontal = ("access_groups",)
    actions = (make_is_enabled_true, make_is_enabled_false)
    inlines = (PersonGroupMemberInline,)

    def get_queryset(self, request):
        queryset = super(PersonGroupAdmin, self).get_queryset(request)
        return queryset.annotate(persons_count=Count("persons"))

    @admin.display(ordering="persons_count", description="#persons")
    def persons_count(self, obj):
        return obj.persons_count


class KeyAdmin(admin.ModelAdmin):
    list_display = ("hwid", "owner", "is_enabled")
    list_filter = ("is_enabled",)
    actions = (make_is_enabled_true, make_is_enabled_false)

    # idea: select form for hwid , from UnknownKeys.
    def render_change_form(self, request, context, *args, **kwargs):
        print("FORMFILED:", context["adminform"].form.fields["hwid"])

        # link from UnknonwnKey list
        if request.GET.get("unknownkey"):
            context["adminform"].form.fields["hwid"].widget.attrs["value"] = (
                request.GET.get("unknownkey")
            )
            context["adminform"].form.fields["hwid"].widget.attrs["readonly"] = True

        # browsing to "new" Key
        elif kwargs["obj"] is None:
            # obj is None -> New
            unknownkeys = [("NOT-SET", "Recent found keys:")]
            for k in LogUnknownKey.objects.order_by("-last_seen"):
                unknownkeys.append(
                    (
                        k.hwid,
                        f"last_seen={k.last_seen.strftime('%H:%M %d-%m-%Y')}, lock={k.lock}, counter={k.counter} , hwid={k.hwid}",
                    )
                )

            context["adminform"].form.fields["hwid"] = forms.ChoiceField(
                help_text="A valid hwid, please.",
                choices=unknownkeys,
                initial="0",
                required=True,
            )

        # browsing to Change key
        else:
            # obj is not None -> Change
            # unknownkeys = [(kwargs['obj'].hwid, kwargs['obj'].hwid )]
            context["adminform"].form.fields["hwid"].widget.attrs["readonly"] = True

        return super(KeyAdmin, self).render_change_form(
            request, context, *args, **kwargs
        )

    # idea: limited to persons with equal groups you are allowed to edit.
    # def render_change_form(self, request, context, *args, **kwargs):
    #     context['adminform'].form.fields['owner'].queryset = Person.objects.filter(name__icontains='D')
    #     return super(KeyAdmin, self).render_change_form(request, context, *args, **kwargs)


class LogUnknownKeyAdmin(admin.ModelAdmin):
    # readonly_fields = []
    list_display = ("hwid", "last_seen", "lock", "counter", "add_to_person")
    readonly_fields = (
        "hwid",
        "last_seen",
        "lock",
        "counter",
    )
    ordering = ("-last_seen",)

    #
    # logUnknownKeys -> http://localhost:8000/admin/doorlockdb/key/add/?unknownkey=123
    #
    @admin.display
    def add_to_person(self, obj):
        if bool(Key.objects.filter(hwid=obj.hwid)):
            return "key already exist"
        else:
            url = reverse("admin:doorlockdb_key_add") + f"?unknownkey={obj.hwid}"
            return format_html(f'<a href="{url}">add to person<a>')

    def has_add_permission(self, request, obj=None):
        return False


class LogKeyLastSeenAdmin(admin.ModelAdmin):
    list_display = (
        "key",
        "lock",
        "owner",
        "counter",
        "last_seen_start",
        "last_seen_end",
    )
    readonly_fields = list_display
    ordering = ("-last_seen_start", "-last_seen_end")

    @admin.display(ordering="key__owner")
    def owner(self, obj):
        return obj.key.owner


class AccessRuleInline(admin.StackedInline):
    model = AccessRule
    max_num = 21
    fieldsets = (
        (
            "edit rule",
            {
                "classes": ("collapse",),
                "fields": (
                    "after",
                    "before",
                    "weekdays_monday",
                    "weekdays_tuesday",
                    "weekdays_wednesday",
                    "weekdays_thursday",
                    "weekdays_friday",
                    "weekdays_saturday",
                    "weekdays_sunday",
                    "time_start",
                    "time_end",
                ),
            },
        ),
    )


class AccessRulesetAdmin(admin.ModelAdmin):
    inlines = [AccessRuleInline]


class AccesGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "rules")
    list_filter = ("locks", "rules")
    filter_horizontal = ("locks",)


class SyncLockKeysAdmin(admin.ModelAdmin):
    list_display = (
        "lock",
        "config_time",
        "last_seen",
        "synchronized",
        "last_sync_keys",
        "last_log_unknownkeys",
        "last_log_keys",
    )
    readonly_fields = (
        "lock",
        "config_time",
        "last_seen",
        "synchronized",
        "last_sync_keys",
        "last_log_unknownkeys",
        "last_log_keys",
        "keys_json",
    )

    def has_add_permission(self, request, obj=None):
        return False


admin.site.register(Lock, LockAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(PersonGroup, PersonGroupAdmin)
admin.site.register(Key, KeyAdmin)
admin.site.register(LogUnknownKey, LogUnknownKeyAdmin)
admin.site.register(LogKeyLastSeen, LogKeyLastSeenAdmin)
admin.site.register(AccessRuleset, AccessRulesetAdmin)
# admin.site.register(AccessRule)
admin.site.register(AccessGroup, AccesGroupAdmin)
admin.site.register(SyncLockKeys, SyncLockKeysAdmin)
