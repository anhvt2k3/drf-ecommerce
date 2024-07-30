from django.db import models

class ModelUtils:
    class IsDeleteHarmonyManager_(models.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(is_deleted=True)
    
    class IsDeleteHarmonyManager(models.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(is_deleted=False)
        
        
        