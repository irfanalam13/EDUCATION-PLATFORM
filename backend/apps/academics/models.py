from django.db import models
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Level(TimeStampedModel):
    name = models.CharField(max_length=50)          # e.g. Class 1, Grade 10, Bachelor 1st
    order = models.PositiveIntegerField(default=0)  # for sorting
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("name",)]

    def __str__(self):
        return self.name


class Stream(TimeStampedModel):
    name = models.CharField(max_length=50)          # e.g. Science, Management, Arts
    code = models.CharField(max_length=20, unique=True)  # e.g. SCI, MGMT
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name


class Subject(TimeStampedModel):
    level = models.ForeignKey(Level, on_delete=models.PROTECT, related_name="subjects")
    stream = models.ForeignKey(
        Stream, on_delete=models.PROTECT, related_name="subjects",
        null=True, blank=True
    )  # optional (some subjects are common)
    name = models.CharField(max_length=100)         # e.g. Mathematics
    code = models.CharField(max_length=30, blank=True, default="")  # optional
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["level", "stream", "name"],
                name="uniq_subject_level_stream_name",
            )
        ]

    def __str__(self):
        if self.stream:
            return f"{self.level} • {self.stream} • {self.name}"
        return f"{self.level} • {self.name}"


class Chapter(TimeStampedModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="chapters")
    title = models.CharField(max_length=200)        # e.g. Algebra
    number = models.PositiveIntegerField(default=0) # chapter number
    order = models.PositiveIntegerField(default=0)  # sorting override
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "number", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["subject", "number"],
                name="uniq_chapter_subject_number",
            )
        ]

    def __str__(self):
        return f"{self.subject} • Ch {self.number}: {self.title}"


class Topic(TimeStampedModel):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=200)        # e.g. Linear Equations
    order = models.PositiveIntegerField(default=0)
    content = models.TextField(blank=True, default="")  # optional notes/theory later
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["chapter", "title"],
                name="uniq_topic_chapter_title",
            )
        ]

    def __str__(self):
        return f"{self.chapter} • {self.title}"


class Tag(TimeStampedModel):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ["name", "id"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:55] or "tag"
            slug = base
            i = 1
            while Tag.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"[:60]
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
