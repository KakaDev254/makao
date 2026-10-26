from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core import views as core_views
from properties import views as property_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth (allauth)
    path("accounts/", include("accounts.urls")),

    # Category landing pages at root
    path("airbnbs/",  property_views.category_landing, {"slug": "airbnb"}, name="airbnbs"),
    path("rentals/",  property_views.category_landing, {"slug": "rental"}, name="rentals"),
    path("land/",     property_views.category_landing, {"slug": "land"},   name="land"),
    path("for-sale/", property_views.category_landing, {"slug": "sale"},   name="for_sale"),

    path("", include("core.urls")),
    path("properties/", include("properties.urls")),

    path("robots.txt", core_views.robots_txt, name="robots_txt"),
    path("sitemap.xml", core_views.sitemap_xml, name="sitemap_xml"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = "core.views.error_404"
handler500 = "core.views.error_500"