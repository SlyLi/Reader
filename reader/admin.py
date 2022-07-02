from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(Book)
admin.site.register(Chapter)
admin.site.register(Content)
admin.site.register(UserBookRecord)