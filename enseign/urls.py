from django.conf.urls import url
from django.contrib import admin
from django.urls import include
from django.utils.translation import gettext as _
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# TODO find a good name
# TODO Write proper description
# TODO have some terms of service
# TODO add good contact info
# TODO add license
swagger_info = openapi.Info(
    title=_('Enseign API'),
    default_version='v1',
    description=_('Calendar API'),
    terms_of_service="https://www.google.com/policies/terms/",
    contact=openapi.Contact(email="contact@concat.contact"),
    license=openapi.License(name="BSD License"),
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
    url('', include('cal.urls')),
]
