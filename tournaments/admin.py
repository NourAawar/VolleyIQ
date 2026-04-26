from django.contrib import admin
from .models import Tournament, Team, TeamMembership, Match, Notification, PerformanceStat

admin.site.register(Tournament)
admin.site.register(Team)
admin.site.register(TeamMembership)
admin.site.register(Match)
admin.site.register(Notification)
admin.site.register(PerformanceStat)