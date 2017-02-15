# Register your models here.
from django.contrib import admin
from .models import Player, Game, Challenge

admin.site.register(Player)
admin.site.register(Game)
admin.site.register(Challenge)


