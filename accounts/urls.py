from django.urls import path, include
from . import views

urlpatterns = [
    # Account Center — names prefixed to avoid clashing with allauth
    path("me/",          views.center_home,     name="account_center_home"),
    path("me/profile/",  views.center_profile,  name="account_center_profile"),
    path("me/password/", views.center_password, name="account_center_password"),
    path("me/delete/",   views.center_delete,   name="account_center_delete"),

    # allauth (unqualified names: account_login, account_logout, etc.)
    path("", include("allauth.urls")),
]