from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_tournament, name='create_tournament'),
    path('list/', views.tournament_list, name='tournament_list'),

    path('teams/', views.team_list, name = 'team_list'), 
    path('teams/create/', views.create_team, name = 'create_team'), 
    path('teams/<int:team_id>/', views.team_detail, name = 'team_detail'), 
]