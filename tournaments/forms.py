from django import forms
from django.contrib.auth.models import User, Group
from .models import Tournament, Team

class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ['name', 'start_date', 'end_date', 'format']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter tournament name'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'format': forms.Select(),
        }

class TeamForm(forms.ModelForm): 
    class Meta: 
        model = Team 
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs = {'placeholder': 'Enter team name'}), 
        }

class AssignCoachForm(forms.ModelForm): 
    class Meta: 
        model = Team 
        fields = ['coach']
        widgets = {
            'coach': forms.Select(), 
        }
    
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)

        try: 
            coach_group = Group.objects.get(name = 'Coach')
            self.fields['coach'].queryset = User.objects.filter(groups = coach_group)

        except Group.DoesNotExist: 
            self.fields['coach'].queryset = User.objects.none()
        
        self.fields['coach'].required = False 
        self.fields['coach'].empty_label = '- Remove coach -'
        