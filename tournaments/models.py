from django.db import models
from django.contrib.auth.models import User

class Tournament(models.Model):
    FORMAT_CHOICES = [
        ('single_elimination', 'Single Elimination'),
        ('double_elimination', 'Double Elimination'),
        ('round_robin', 'Round Robin'),
    ]

    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    format = models.CharField(max_length=50, choices=FORMAT_CHOICES)
    teams = models.ManyToManyField(
        'Team', 
        blank = True, 
        related_name = 'tournaments', 
    )

    def __str__(self):
        return self.name

class Team(models.Model): 
    name = models.CharField(max_length = 100)

    coach = models.ForeignKey(
        User, 
        null = True, 
        blank = True, 
        on_delete = models.SET_NULL, 
        related_name = 'coached_teams', 
        limit_choices_to = {'groups__name': 'Coach'}, 
    )

    def __str__(self): 
        return self.name
    
class TeamMembership(models.Model): 
    POSITION_CHOICES = [
        ('setter', 'Setter'), 
        ('outside_hitter', 'Outside Hitter'), 
        ('opposite', 'Opposite Hitter'), 
        ('middle_blocker', 'Middle Blocker'), 
        ('libero', 'Libero'), 
        ('defensive_specialist', 'Defensive Specialist'), 
    ]

    team = models.ForeignKey(Team, on_delete = models.CASCADE, related_name = 'memberships')
    player = models.ForeignKey(
        User, 
        on_delete = models.CASCADE, 
        related_name = 'team_memberships', 
        limit_choices_to = {'groups__name': 'Player'}, 
    )
    position = models.CharField(max_length = 50, choices = POSITION_CHOICES, blank = True)
    jersey_number = models.PositiveIntegerField(null = True, blank = True)

    class Meta: 
        unique_together = ('team', 'player')
    
    def __str__(self): 
        return f"{self.player.username} → {self.team.name}"