from django.contrib import admin

from .models import Schema, Table, Column

admin.site.register(Schema)
admin.site.register(Table)
admin.site.register(Column)
