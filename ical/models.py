from django.db.models import Model, CharField, DateTimeField


class Event(Model):
    name = CharField(max_length=255)
    date = DateTimeField()
    description = CharField(max_length=255)
