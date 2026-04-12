import uuid
from django.utils import timezone
from django.db import models


class TouchDatesMixim(models.Model):
    """
    Add id(uuid4), created_at and updated_at support for models
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField("Date Created", auto_now_add=True, null=True)
    updated_at = models.DateTimeField("Date Updated", auto_now=True, null=True)
    is_fake_data = models.BooleanField(default=False)

    # class Meta(auto_prefetch.Model.Meta):
    #     abstract = True
    class Meta:
        """meta class"""

        abstract = True


class SoftDeleteModelManager(models.Manager):
    """ " Soft delete manager class"""

    def get_queryset(self):

        return super().get_queryset().filter(soft_delete=False)


class SoftDeleteModel(models.Model):
    """softdelete abs class"""

    soft_delete = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True

    def delete(self):
        self.soft_delete = True
        self.deleted_at = timezone.now()
        self.save()
