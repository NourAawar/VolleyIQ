from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import TournamentForm
from .models import Tournament


def home(request):
    is_club_manager = False
    is_coach = False
    is_player = False

    if request.user.is_authenticated:
        is_club_manager = request.user.groups.filter(name='Club Manager').exists()
        is_coach = request.user.groups.filter(name='Coach').exists()
        is_player = request.user.groups.filter(name='Player').exists()

    return render(request, 'tournaments/home.html', {
        'is_club_manager': is_club_manager,
        'is_coach': is_coach,
        'is_player': is_player,
    })


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