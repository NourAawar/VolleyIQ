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

    class Meta:
        ordering = ['-points', '-wins']

    coach = models.ForeignKey(
        User, 
        null = True, 
        blank = True, 
        on_delete = models.SET_NULL, 
        related_name = 'coached_teams', 
        limit_choices_to = {'groups__name': 'Coach'},
    )

    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    points = models.IntegerField(default=0)

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
    
class Match(models.Model):
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='matches'
    )
    home_team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='home_matches'
    )
    away_team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='away_matches'
    )
    match_date = models.DateField()
    match_time = models.TimeField()
    venue = models.CharField(max_length=150, default='Main Court')

    home_score = models.PositiveIntegerField(null=True, blank=True)
    away_score = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['match_date', 'match_time']

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} - {self.tournament.name}"
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)



    def __str__(self):
        return f"To {self.user.username}: {self.message}"
    
class PerformanceStat(models.Model):
    PERIOD_CHOICES = [
        ('set_1', 'Set 1'),
        ('set_2', 'Set 2'),
        ('set_3', 'Set 3'),
        ('set_4', 'Set 4'),
        ('set_5', 'Set 5'),
        ('full_match', 'Full Match'),
    ]

    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name='performance_stats'
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='performance_stats'
    )

    player = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='performance_stats',
        null=True,
        blank=True,
        limit_choices_to={'groups__name': 'Player'}
    )

    period = models.CharField(
        max_length=20,
        choices=PERIOD_CHOICES,
        default='full_match'
    )

    kills = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    blocks = models.PositiveIntegerField(default=0)
    digs = models.PositiveIntegerField(default=0)
    aces = models.PositiveIntegerField(default=0)
    errors = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def total_points(self):
        return self.kills + self.blocks + self.aces

    def __str__(self):
        if self.player:
            return f"{self.player.username} - {self.team.name} - {self.get_period_display()}"
        return f"{self.team.name} Team Stat - {self.get_period_display()}"