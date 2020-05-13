from django.apps import AppConfig


class ScolendarConfig(AppConfig):
    name = 'scolendar'

    def ready(self):
        import scolendar.signals
