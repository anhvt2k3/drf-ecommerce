from django.db import models
from eco_sys.model_utils import ModelUtils

class ChildrenOfTableMixin:

    @classmethod
    def get_table_field(cls, target_model: models.Model) -> tuple[models.Field, str] | None:
        """
            Get the field name of the field that point to the target model.
        """

        for field in cls._meta.get_fields():
            if field.related_model == target_model:
                return field.name
        return None

class BasicManager(models.Manager):
    def _base_queryset(self):
        return super().get_queryset()

class SoftDeleteManager(BasicManager):
    def get_queryset(self):
        qs = self._base_queryset().filter(is_deleted=False)
        return qs

class SoftDeleteManager_(BasicManager):
    def get_queryset(self):
        qs = self._base_queryset().filter(is_deleted=True)
        return qs

class SoftDeleteModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    objects = SoftDeleteManager()
    deleted = SoftDeleteManager_()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.save()
        
    def restore(self):
        self.is_deleted = False
        self.save()

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)
