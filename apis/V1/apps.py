from django.apps import AppConfig


class V1Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # Keep the import path, but set an explicit app label (no dots) so
    # Django can reliably reference models before full app population.
    name = 'apis.V1'
    label = 'apis_v1'
    verbose_name = 'APIs V1'
