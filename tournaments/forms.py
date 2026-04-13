from django import forms
from django.contrib.auth.models import User, Group
from .models import Tournament, Team, TeamMembership, Match

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

class AddPlayerForm(forms.ModelForm): 
    class Meta: 
        model = TeamMembership
        fields = ['player', 'position', 'jersey_number']
        widgets = {
            'player': forms.Select(), 
            'position': forms.Select(), 
            'jersey_number': forms.NumberInput(attrs = {'placeholder': 'Jersey number (optional)'}), 
        }

    def __init__(self, *args, team = None, **kwargs): 
        super().__init__(*args, **kwargs)

        try: 
            player_group = Group.objects.get(name = 'Player')
            already_added = []

            if team: 
                already_added = team.memberships.values_list('player_id', flat = True)
                
            self.fields['player'].queryset = User.objects.filter(
                groups = player_group
            ).exclude(id__in = already_added)
            
        except Group.DoesNotExist: 
            self.fields['player'].queryset = User.objects.none()
            
        self.fields['position'].required = False 
        self.fields['jersey_number'].required = False 

class RegisterTeamForm(forms.Form): 
    team = forms.ModelChoiceField(
        queryset = Team.objects.none(), 
        empty_label = '- Select a team -', 
        widget = forms.Select(), 
    )

    def __init__(self, *args, tournament = None, **kwargs): 
        super().__init__(*args, **kwargs)

        if tournament: 
            already_registered = tournament.teams.values_list('id', flat = True)
            self.fields['team'].queryset = Team.objects.exclude(id__in = already_registered)

class EditMatchTimeForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['match_date', 'match_time']
        widgets = {
            'match_date': forms.DateInput(attrs={'type': 'date'}),
            'match_time': forms.TimeInput(attrs={'type': 'time'}),
        }


class UpdateMatchVenueForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['venue']
        widgets = {
            'venue': forms.TextInput(attrs={'placeholder': 'Enter new venue'}),
        }