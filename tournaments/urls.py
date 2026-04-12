from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_tournament, name='create_tournament'),
    path('list/', views.tournament_list, name='tournament_list'),
]