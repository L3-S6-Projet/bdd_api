from django.conf.urls import url

from ical.views import EventFeed

urlpatterns = [
    url(r'^latest/feed.ics$', EventFeed()),
]
