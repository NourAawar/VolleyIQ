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

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date cannot be before start date.")
        return cleaned_data

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

    def clean_match_date(self):
        match_date = self.cleaned_data.get('match_date')
        if match_date and self.instance and self.instance.pk:
            tournament = self.instance.tournament
            if match_date < tournament.start_date:
                raise forms.ValidationError(
                    f"Match date cannot be before the tournament start date ({tournament.start_date})."
                )
            if match_date > tournament.end_date:
                raise forms.ValidationError(
                    f"Match date cannot be after the tournament end date ({tournament.end_date})."
                )
        return match_date


class UpdateMatchVenueForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['venue']
        widgets = {
            'venue': forms.TextInput(attrs={'placeholder': 'Enter new venue'}),
        }

class MatchScoreForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['home_score', 'away_score']
        widgets = {
            'home_score': forms.NumberInput(attrs={'placeholder': 'Home team score'}),
            'away_score': forms.NumberInput(attrs={'placeholder': 'Away team score'}),
        }