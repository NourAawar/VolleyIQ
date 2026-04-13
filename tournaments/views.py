from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import TournamentForm, TeamForm, AssignCoachForm, AddPlayerForm, RegisterTeamForm
from .models import Tournament, Team, TeamMembership

def is_club_manager(user): 
    return user.groups.filter(name = 'Club Manager').exists()

def home(request):
    return render(request, 'tournaments/home.html')

@login_required
def create_tournament(request):
    if not request.user.groups.filter(name='Club Manager').exists():
        return HttpResponseForbidden("Only Club Managers can create tournaments.")

    if request.method == 'POST':
        form = TournamentForm(request.POST)
        if form.is_valid(): 
            form.save()
            return redirect('tournament_list')
    else:
        form = TournamentForm()

    return render(request, 'tournaments/create_tournament.html', {'form': form})

@login_required
def tournament_list(request):
    tournaments = Tournament.objects.all()
    return render(request, 'tournaments/tournament_list.html', {'tournaments': tournaments})

@login_required 
def tournament_detail(request, tournament_id):
    tournament = get_object_or_404(Tournament, id = tournament_id)
    registered_teams = tournament.teams.select_related('coach')

    return render(request, 'tournaments/tournament_detail.html', {
        'tournament': tournament, 
        'registered_teams': registered_teams,
    })

@login_required
def register_team(request, tournament_id): 
    if not is_club_manager(request.user): 
        return HttpResponseForbidden("Only Club Managers can register teams.")
    
    tournament = get_object_or_404(Tournament, id = tournament_id)

    if request.method == 'POST': 
        form = RegisterTeamForm(request.POST, tournament = tournament)
        if form.is_valid(): 
            team = form.cleaned_data['team']
            tournament.teams.add(team)

            return redirect('tournament_detail', tournament_id = tournament.id)
    
    else: 
        form = RegisterTeamForm(tournament = tournament)
    
    return render(request, 'tournaments/register_team.html', {
        'form': form, 
        'tournament': tournament, 
    })

@login_required 
def team_list(request): 
    teams = Team.objects.all()

    return render(request, 'tournaments/team_list.html', {'teams': teams})

@login_required 
def create_team(request): 
    if not is_club_manager(request.user): 
        return HttpResponseForbidden("Only Club Managers can create teams.")
    
    if request.method == 'POST': 
        form = TeamForm(request.POST)
        if form.is_valid(): 
            form.save()

            return redirect('team_list')
    
    else: 
        form = TeamForm()

    return render(request, 'tournaments/create_team.html', {'form': form})

@login_required 
def team_detail(request, team_id): 
    team = get_object_or_404(Team, id = team_id)
    memberships = team.memberships.select_related('player')

    return render(request, 'tournaments/team_detail.html', {'team': team, 'memberships': memberships})

@login_required 
def assign_coach(request, team_id): 
    if not is_club_manager(request.user): 
        return HttpResponseForbidden("Only Club Managers can assign coaches.")
    
    team = get_object_or_404(Team, id = team_id)

    if request.method == 'POST': 
        form = AssignCoachForm(request.POST, instance = team)
        if form.is_valid(): 
            form.save()

            return redirect('team_detail', team_id = team.id)
        
    else: 
        form = AssignCoachForm(instance = team)
        
    return render(request, 'tournaments/assign_coach.html', {'form': form, 'team': team})

@login_required 
def add_player(request, team_id): 
    if not is_club_manager(request.user): 
        return HttpResponseForbidden("Only Club Managers can add players.")
    
    team = get_object_or_404(Team, id = team_id)

    if request.method == 'POST': 
        form = AddPlayerForm(request.POST, team = team)
        if form.is_valid(): 
            membership = form.save(commit = False)
            membership.team = team 
            membership.save()

            return redirect('team_detail', team_id = team.id)
    
    else: 
        form = AddPlayerForm(team = team)

    return render(request, 'tournaments/add_player.html', {'form': form, 'team': team})

@login_required 
def remove_player(request, team_id, membership_id): 
    if not is_club_manager(request.user): 
        return HttpResponseForbidden("Only Club Managers can remove players.")
    
    team = get_object_or_404(Team, id = team_id)
    membership = get_object_or_404(TeamMembership, id = membership_id, team = team)

    if request.method == 'POST': 
        membership.delete()

        return redirect('team_detail', team_id = team.id)
    
    return render(request, 'tournaments/confirm_remove_player.html', {'team': team, 'membership': membership,})