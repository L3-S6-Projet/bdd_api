from django_ical.views import ICalFeed

from ical.models import Event


class EventFeed(ICalFeed):
    """
    A simple event calender
    """
    product_id = '-//example.com//Example//EN'
    timezone = 'UTC'
    file_name = "event.ics"

    def __call__(self, request, *args, **kwargs):
        return super(EventFeed, self).__call__(request, *args, **kwargs)

    def items(self):
        return Event.objects.all().order_by('-date')

    def item_guid(self, item):
        return f'{item.id}'

    def item_title(self, item):
        return item.name

    def item_description(self, item):
        return item.description

    def item_start_datetime(self, item):
        return item.date

    def item_link(self, item):
        return "http://www.google.de"
