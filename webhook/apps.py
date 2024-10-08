from django import apps

class WebhookConfig(apps.AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'webhook'