from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import TournamentForm
from .models import Tournament

def home(request):
    return render(request, 'tournaments/home.html')

def create_tournament(request):
    if request.method == 'POST':
        form = TournamentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tournament_list')
    else:
        form = TournamentForm()

    return render(request, 'tournaments/create_tournament.html', {'form': form})

def tournament_list(request):
    tournaments = Tournament.objects.all()
    return render(request, 'tournaments/tournament_list.html', {'tournaments': tournaments})