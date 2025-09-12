from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("select-action/", views.select_action_view, name="select_action"),
    path("select-receiver/", views.select_receiver_view, name="select_receiver"),
    path("upload/<int:receiver_id>/", views.upload_document_view, name="upload_document"),
    path("decrypt/", views.decrypt_document_view, name="decrypt_document"),
]
