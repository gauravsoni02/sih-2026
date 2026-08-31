from django.db import models


class TimeStampedQuerySet(models.QuerySet):
    def active(self) -> models.QuerySet:
        return self.filter(is_deleted=False)


class TimeStampedManager(models.Manager):
    def get_queryset(self) -> TimeStampedQuerySet:
        return TimeStampedQuerySet(self.model, using=self._db)

    def active(self) -> TimeStampedQuerySet:
        return self.get_queryset().active()


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    objects = TimeStampedManager()

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])
