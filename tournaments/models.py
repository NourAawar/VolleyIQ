from django.db import models

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
    