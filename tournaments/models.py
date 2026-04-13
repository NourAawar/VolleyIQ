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