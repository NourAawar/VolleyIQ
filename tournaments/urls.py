from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('create/', views.create_tournament, name='create_tournament'),
    path('list/', views.tournament_list, name='tournament_list'),

    path('tournaments/<int:tournament_id>/', views.tournament_detail, name='tournament_detail'),
    path('tournaments/<int:tournament_id>/delete/', views.delete_tournament, name='delete_tournament'),
    path('tournaments/<int:tournament_id>/register-team/', views.register_team, name='register_team'),
    path('tournaments/<int:tournament_id>/remove-team/<int:team_id>/', views.remove_team, name='remove_team'),
    path('tournaments/<int:tournament_id>/generate-schedule/', views.generate_schedule, name='generate_schedule'),
    path('tournaments/<int:tournament_id>/advance-round/', views.advance_round, name='advance_round'),

    path('teams/', views.team_list, name='team_list'),
    path('teams/create/', views.create_team, name='create_team'),
    path('teams/<int:team_id>/', views.team_detail, name='team_detail'),
    path('teams/<int:team_id>/assign-coach/', views.assign_coach, name='assign_coach'),
    path('teams/<int:team_id>/add-player/', views.add_player, name='add_player'),
    path('teams/<int:team_id>/remove-player/<int:membership_id>/', views.remove_player, name='remove_player'),
    path('teams/<int:team_id>/assign-task/', views.assign_task, name='assign_task'),
    path('teams/<int:team_id>/tasks/', views.team_tasks, name='team_tasks'),

    path('matches/<int:match_id>/edit-time/', views.edit_match_time, name='edit_match_time'),
    path('matches/<int:match_id>/update-venue/', views.update_match_venue, name='update_match_venue'),
    path('matches/<int:match_id>/score/', views.update_match_score, name='update_match_score'),
    path('matches/<int:match_id>/availability/', views.match_availability, name='match_availability'),
    path('matches/<int:match_id>/attendance/', views.record_attendance, name='record_attendance'),

    path('teams/<int:team_id>/schedule/', views.team_match_schedule, name='team_match_schedule'),
    path('my-performance/', views.player_performance, name='player_performance'),
    path('teams/<int:team_id>/performance/', views.team_performance, name='team_performance'),
    path('my-tasks/', views.my_tasks, name='my_tasks'),

    path('teams/<int:team_id>/send-message/', views.send_team_message, name = 'send_team_message'),
    path('announcements/send/', views.send_announcement, name = 'send_announcement'),
    path('announcements/', views.team_announcements_all, name = 'team_announcements_all'),
]