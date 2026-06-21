# apps/gamification/models.py
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


User = settings.AUTH_USER_MODEL


class UserGamificationProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="gami_profile")

    total_xp = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)

    streak_days = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)  # local-day concept handled in service
    freeze_tokens = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"GamificationProfile(user={self.user_id}, level={self.level}, xp={self.total_xp})"


class UserLevel(models.Model):
    """
    Optional. If you prefer, you can remove this model and store everything in profile.
    Keeping it to match your original plan and enable future analytics.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_level")
    level = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"UserLevel(user={self.user_id}, level={self.level})"


class XpDailyCap(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="xp_caps")
    date = models.DateField(db_index=True)
    source = models.CharField(max_length=64, db_index=True)
    used_points = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("user", "date", "source")]

    def __str__(self) -> str:
        return f"XpDailyCap(user={self.user_id}, {self.date}, {self.source}, used={self.used_points})"


class XpTransaction(models.Model):
    STATUS_AWARDED = "awarded"
    STATUS_BLOCKED = "blocked"
    STATUS_REVERTED = "reverted"

    STATUS_CHOICES = [
        (STATUS_AWARDED, "Awarded"),
        (STATUS_BLOCKED, "Blocked"),
        (STATUS_REVERTED, "Reverted"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="xp_transactions")
    created_at = models.DateTimeField(auto_now_add=True)

    source = models.CharField(max_length=64, db_index=True)

    # generic reference without GFK: keep it simple & fast
    object_type = models.CharField(max_length=64, blank=True, default="")
    object_id = models.CharField(max_length=64, blank=True, default="")

    points_base = models.IntegerField(default=0)     # can be negative for revert
    points_awarded = models.IntegerField(default=0)  # after caps/multipliers
    multiplier = models.DecimalField(max_digits=6, decimal_places=2, default=1.00)

    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_AWARDED)

    idempotency_key = models.CharField(max_length=128, blank=True, default="", db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["source", "created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "source", "idempotency_key"],
                condition=~models.Q(idempotency_key=""),
                name="uniq_user_source_idempotency_nonempty",
            )
        ]

    def __str__(self) -> str:
        return f"XpTx(user={self.user_id}, src={self.source}, pts={self.points_awarded}, st={self.status})"


class Badge(models.Model):
    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    icon = models.CharField(max_length=255, blank=True, default="")  # store icon key/path
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # criteria stored in JSON to match rulebook
    criteria = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"Badge({self.code})"


class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="badges")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="user_badges")
    awarded_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [("user", "badge")]

    def __str__(self) -> str:
        return f"UserBadge(user={self.user_id}, badge={self.badge.code})"


class Quest(models.Model):
    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    # e.g. {"type":"daily","target":10,"source":"practice_correct"}
    rules = models.JSONField(default=dict, blank=True)

    # reward definition
    reward = models.JSONField(default=dict, blank=True)  # e.g. {"xp":50}

    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Quest({self.code})"


class UserQuestProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quest_progress")
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name="progress_rows")

    progress = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    is_claimed = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("user", "quest")]

    def __str__(self) -> str:
        return f"UserQuestProgress(user={self.user_id}, quest={self.quest.code}, p={self.progress})"


class LeaderboardEntry(models.Model):
    PERIOD_WEEKLY = "weekly"
    PERIOD_MONTHLY = "monthly"
    PERIOD_ALL_TIME = "all_time"

    PERIOD_CHOICES = [
        (PERIOD_WEEKLY, "Weekly"),
        (PERIOD_MONTHLY, "Monthly"),
        (PERIOD_ALL_TIME, "All time"),
    ]

    SCOPE_GLOBAL = "global"
    SCOPE_INSTITUTION = "institution"
    SCOPE_COHORT = "cohort"

    SCOPE_CHOICES = [
        (SCOPE_GLOBAL, "Global"),
        (SCOPE_INSTITUTION, "Institution"),
        (SCOPE_COHORT, "Cohort"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="leaderboard_entries")
    scope = models.CharField(max_length=32, choices=SCOPE_CHOICES, default=SCOPE_GLOBAL)
    scope_id = models.CharField(max_length=64, blank=True, default="")  # "" for global

    period = models.CharField(max_length=16, choices=PERIOD_CHOICES, default=PERIOD_WEEKLY)
    period_key = models.CharField(max_length=32, db_index=True)  # e.g. "2026-W05", "2026-01", "all"

    xp_total = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("user", "scope", "scope_id", "period", "period_key")]
        indexes = [
            models.Index(fields=["scope", "scope_id", "period", "period_key", "-xp_total"]),
        ]

    def __str__(self) -> str:
        return f"LB(user={self.user_id}, {self.scope}:{self.scope_id}, {self.period}:{self.period_key}, xp={self.xp_total})"
