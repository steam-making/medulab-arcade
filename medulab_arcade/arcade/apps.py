from django.apps import AppConfig

class ArcadeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'arcade'
    verbose_name = '학생 아케이드'

    def ready(self):
        import arcade.models  # noqa: F401 — signal 등록 보장
