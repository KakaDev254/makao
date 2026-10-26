from django.urls import path
from . import views

app_name = "properties"

urlpatterns = [
    path("listings/", views.listings, name="listings"),
    path("by-slugs/", views.listings_by_slugs, name="by_slugs"),

    # Saved properties API
    path("saved/slugs/",  views.saved_slugs, name="saved_slugs"),
    path("saved/toggle/", views.save_toggle, name="save_toggle"),
    path("saved/merge/",  views.saved_merge,  name="saved_merge"),

    # Agents
    path("agents/<slug:slug>/", views.agent_detail, name="agent_detail"),

    # Category landing pages
    path("airbnbs/",   views.category_landing, {"slug": "airbnb"}, name="airbnbs"),
    path("rentals/",   views.category_landing, {"slug": "rental"}, name="rentals"),
    path("land/",      views.category_landing, {"slug": "land"},   name="land"),
    path("for-sale/",  views.category_landing, {"slug": "sale"},   name="for_sale"),

    # Submission flow
    path("submit/",         views.submit_property, name="submit"),
    path("submit/success/", views.submit_success,  name="submit_success"),

    # Detail endpoints
    path("<slug:slug>/json/", views.property_detail_json, name="detail_json"),
    path("<slug:slug>/",      views.property_detail,      name="detail"),
]