from django.contrib import admin
from .models import Team,Players


@admin.register(Team)
class Teamadmin(admin.ModelAdmin):
    list_display= ('name','city')
    search_fields=('name','city')
@admin.register(Players)
class Playersadmin(admin.ModelAdmin):
    list_display=('name','age','experience','role','shirt_no')
    list_filter = ('team', 'role')
    search_fields = ('name', 'team__name')