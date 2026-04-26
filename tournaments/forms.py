from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from .models import Tournament, Team, TeamMembership, Match, Task, PlayerAvailability, Attendance, Announcement

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
            'name': forms.TextInput(attrs={'placeholder': 'Enter team name'}),
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
            coach_group = Group.objects.get(name='Coach')
            self.fields['coach'].queryset = User.objects.filter(groups=coach_group)
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
            'jersey_number': forms.NumberInput(attrs={'placeholder': 'Jersey number (optional)'}),
        }

    def __init__(self, *args, team=None, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            player_group = Group.objects.get(name='Player')
            already_added = team.memberships.values_list('player_id', flat=True) if team else []
            self.fields['player'].queryset = User.objects.filter(
                groups=player_group
            ).exclude(id__in=already_added)
        except Group.DoesNotExist:
            self.fields['player'].queryset = User.objects.none()
        self.fields['position'].required = False
        self.fields['jersey_number'].required = False

class RegisterTeamForm(forms.Form):
    team = forms.ModelChoiceField(
        queryset=Team.objects.none(),
        empty_label='- Select a team -',
        widget=forms.Select(),
    )

    def __init__(self, *args, tournament=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tournament:
            already_registered = tournament.teams.values_list('id', flat=True)
            self.fields['team'].queryset = Team.objects.exclude(id__in=already_registered)

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

class AssignTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Task title'}),
            'description': forms.Textarea(attrs={'placeholder': 'Task description (optional)', 'rows': 3}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, team=None, **kwargs):
        super().__init__(*args, **kwargs)
        if team:
            player_ids = team.memberships.values_list('player_id', flat=True)
            self.fields['assigned_to'].queryset = User.objects.filter(id__in=player_ids)
        else:
            self.fields['assigned_to'].queryset = User.objects.none()
        self.fields['description'].required = False
        self.fields['due_date'].required = False

class PlayerAvailabilityForm(forms.ModelForm):
    class Meta:
        model = PlayerAvailability
        fields = ['status', 'note']
        widgets = {
            'note': forms.TextInput(attrs={'placeholder': 'Optional note'}),
        }

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['status', 'note']
        widgets = {
            'note': forms.TextInput(attrs={'placeholder': 'Optional note'}),
        }


class RegistrationForm(UserCreationForm):
    ROLE_CHOICES = [
        ('Player', 'Player'),
        ('Coach', 'Coach'),
        ('Club Manager', 'Club Manager'),
    ]
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select())

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            role_name = self.cleaned_data['role']
            group, _ = Group.objects.get_or_create(name=role_name)
            user.groups.add(group)
        return user


class CreatePlayerForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'placeholder': 'Last name'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'placeholder': 'Email (optional)'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            group, _ = Group.objects.get_or_create(name='Player')
            user.groups.add(group)
        return user


class TeamMessageForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'body']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Message title'}),
            'body': forms.Textarea(attrs={'placeholder': 'Write your message...', 'rows': 4}),
        }

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'body']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Announcement title'}),
            'body': forms.Textarea(attrs={'placeholder': 'Write your announcement...', 'rows': 4}),
        }