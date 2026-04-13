from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_tournament, name='create_tournament'),
    path('list/', views.tournament_list, name='tournament_list'),

    path('tournaments/<int:tournament_id>/', views.tournament_detail, name = 'tournament_detail'), 
    path('tournaments/<int:tournament_id>/register-team/', views.register_team, name = 'register_team'), 
    path('tournaments/<int:tournament_id>/remove-team/<int:team_id>/', views.remove_team, name = 'remove_team'), 

    path('teams/', views.team_list, name = 'team_list'), 
    path('teams/create/', views.create_team, name = 'create_team'), 
    path('teams/<int:team_id>/', views.team_detail, name = 'team_detail'), 
    path('teams/<int:team_id>/assign-coach/', views.assign_coach, name = 'assign_coach'), 
    path('teams/<int:team_id>/add-player/', views.add_player, name = 'add_player'), 
    path('teams/<int:team_id>/remove-player/<int:membership_id>/', views.remove_player, name = 'remove_player'), 
]