from django.conf.urls import url
from django.contrib import admin
from django.urls import include
from django.utils.translation import gettext as _
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

swagger_info = openapi.Info(
    title=_('Scolendar API'),
    default_version='1.0.0',
    description=_(
        'UE Projet - L3 Informatique AMU 2019-2020\nAll of the routes missing the `role-professor` or `role-student` tags are meant for administrators only - as stated in their descriptions.'),
)

schema_view = get_schema_view(
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^grappelli/', include('grappelli.urls')),

    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^api/', include('scolendar.urls')),
]
