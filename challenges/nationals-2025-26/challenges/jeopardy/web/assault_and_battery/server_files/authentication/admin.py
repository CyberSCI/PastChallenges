from django.contrib import admin

from authentication.models import UserEncryptionKey

admin.site.register(UserEncryptionKey)
