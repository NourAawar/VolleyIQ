from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import TournamentForm, TeamForm
from .models import Tournament, Team

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

    return render(request, 'tournaments/team_detail.html', {'team': team})