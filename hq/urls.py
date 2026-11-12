from django.urls import path
from . import views

app_name = "hq"
urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("logout/", views.logout_view, name="logout"),
    path("messages/", views.messages_home, name="messages"),
    path("messages/<str:codename>/", views.thread, name="thread"),
    path("equipment/", views.equipment, name="equipment"),
    path("equipment/<int:pk>/report/", views.equipment_report, name="equipment_report"),
    path("training/", views.training, name="training"),
    path("profile/", views.profile, name="profile"),
]