from django.contrib import admin
from .models import Meeting, AgendaItem, Member, Organization


class AgendaItemInline(admin.TabularInline):
    model = AgendaItem
    extra = 1


class MeetingAdmin(admin.ModelAdmin):
    inlines = [AgendaItemInline]
    list_display = ('title', 'date')
    search_fields = ('title', 'date')
    date_hierarchy = 'date'
    ordering = ('-date',)

class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')


admin.site.register(Meeting, MeetingAdmin)
admin.site.register(Member)
admin.site.register(Organization, OrganizationAdmin)