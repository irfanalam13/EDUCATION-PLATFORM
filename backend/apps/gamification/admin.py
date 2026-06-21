# apps/gamification/admin.py
from django.contrib import admin
from apps.gamification.models import (
    UserGamificationProfile, UserLevel, XpTransaction, XpDailyCap,
    Badge, UserBadge, Quest, UserQuestProgress, LeaderboardEntry
)

@admin.register(UserGamificationProfile)
class UserGamificationProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "level", "total_xp", "streak_days", "longest_streak", "updated_at")
    search_fields = ("user__username", "user__email")


admin.site.register(UserLevel)
admin.site.register(XpDailyCap)
admin.site.register(XpTransaction)
admin.site.register(Badge)
admin.site.register(UserBadge)
admin.site.register(Quest)
admin.site.register(UserQuestProgress)
admin.site.register(LeaderboardEntry)
