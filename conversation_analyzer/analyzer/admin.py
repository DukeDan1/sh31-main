'''Settings for Django's admin panel.'''

from django.contrib import admin
from analyzer.models import SystemUser

admin.site.register(SystemUser)
