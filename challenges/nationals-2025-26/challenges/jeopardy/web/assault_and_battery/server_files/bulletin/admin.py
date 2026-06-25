from django.contrib import admin

from bulletin.models import Bulletin, BulletinPost, Comment, SharedPostAccess

# Register your models here.

admin.site.register(Bulletin)
admin.site.register(BulletinPost)
admin.site.register(Comment)
admin.site.register(SharedPostAccess)
