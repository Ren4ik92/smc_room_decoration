from django.apps import AppConfig


def create_moderator_group(sender, **kwargs):
    """Создает группу 'Editor', если она отсутствует"""
    from django.contrib.auth.models import Group  # Переносим импорт сюда

    group_name = "Editor"
    if not Group.objects.filter(name=group_name).exists():
        Group.objects.create(name=group_name)


class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "main"

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(create_moderator_group, sender=self)