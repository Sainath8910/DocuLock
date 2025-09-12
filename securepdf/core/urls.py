# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('question/', views.random_question, name='random_question'),
]
