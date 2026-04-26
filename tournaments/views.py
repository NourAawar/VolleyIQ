from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import (
    TournamentForm, TeamForm, AssignCoachForm, AddPlayerForm,
    RegisterTeamForm, EditMatchTimeForm, UpdateMatchVenueForm,
    MatchScoreForm
)
from .models import Tournament, Team, TeamMembership, Match, Notification, PerformanceStat
from django.contrib import messages
from datetime import timedelta, time, date
from django.db import models
from django.db.models import Sum


def is_coach(user):
    return user.groups.filter(name='Coach').exists()


def is_player(user):
    return user.groups.filter(name='Player').exists()


def is_club_manager(user):
    return user.groups.filter(name='Club Manager').exists()


def home(request):
    notifications = []

    if request.user.is_authenticated:
        notifications = request.user.notifications.order_by('-created_at')[:5]

    return render(request, 'tournaments/home.html', {
        'notifications': notifications,
    })


@login_required
def create_tournament(request):
    if not is_club_manager(request.user):
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
def delete_tournament(request, tournament_id):
    if not is_club_manager(request.user):
        return HttpResponseForbidden("Only Club Managers can delete tournaments.")

    tournament = get_object_or_404(Tournament, id=tournament_id)

    if request.method == 'POST':
        tournament.delete()
        messages.success(request, f"Tournament '{tournament.name}' has been deleted.")
        return redirect('tournament_list')

    return render(request, 'tournaments/confirm_delete_tournament.html', {
        'tournament': tournament,
    })


@login_required
def tournament_list(request):
    tournaments = Tournament.objects.all()
    return render(request, 'tournaments/tournament_list.html', {'tournaments': tournaments})


@login_required
def tournament_detail(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)

    registered_teams = tournament.teams.all().order_by('-points', '-wins')

    matches = tournament.matches.select_related(
        'home_team',
        'away_team'
    )

    standings = tournament.teams.order_by(
        '-points',
        '-wins'
    )

    return render(request, 'tournaments/tournament_detail.html', {
        'tournament': tournament,
        'registered_teams': registered_teams,
        'matches': matches,
        'standings': standings,
        'today': date.today(),
    })


@login_required
def register_team(request, tournament_id):
    if not is_club_manager(request.user):
        return HttpResponseForbidden("Only Club Managers can register teams.")

    tournament = get_object_or_404(Tournament, id=tournament_id)

    if tournament.start_date <= date.today():
        messages.error(request, "Cannot register teams after the tournament has already started.")
        return redirect('tournament_detail', tournament_id=tournament.id)

    if request.method == 'POST':
        form = RegisterTeamForm(request.POST, tournament=tournament)
        if form.is_valid():
            team = form.cleaned_data['team']
            tournament.teams.add(team)
            return redirect('tournament_detail', tournament_id=tournament.id)
    else:
        form = RegisterTeamForm(tournament=tournament)

    return render(request, 'tournaments/register_team.html', {
        'form': form,
        'tournament': tournament,
    })


@login_required
def remove_team(request, tournament_id, team_id):
    if not is_club_manager(request.user):
        return HttpResponseForbidden("Only Club Managers can remove teams.")

    tournament = get_object_or_404(Tournament, id=tournament_id)
    team = get_object_or_404(Team, id=team_id)

    team_has_matches = tournament.matches.filter(
        models.Q(home_team=team) | models.Q(away_team=team)
    ).exists()

    if team_has_matches:
        messages.error(request, "Cannot remove a team after the schedule has been generated.")
        return redirect('tournament_detail', tournament_id=tournament.id)

    if request.method == 'POST':
        tournament.teams.remove(team)
        messages.success(request, "Team removed from tournament successfully.")
        return redirect('tournament_detail', tournament_id=tournament.id)

    return render(request, 'tournaments/confirm_remove_team.html', {
        'tournament': tournament,
        'team': team,
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
    team = get_object_or_404(Team, id=team_id)
    memberships = team.memberships.select_related('player')

    matches = Match.objects.filter(
        models.Q(home_team=team) | models.Q(away_team=team)
    ).order_by('-match_date')

    last_matches = matches[:3]

    trend = []
    for m in last_matches:
        if m.home_score is None or m.away_score is None:
            continue

        if m.home_team == team:
            trend.append("W" if m.home_score > m.away_score else "L")
        else:
            trend.append("W" if m.away_score > m.home_score else "L")

    trend = trend[::-1]

    wins_count = trend.count("W")
    losses_count = trend.count("L")

    if not trend:
        performance = "No data yet"
    elif wins_count > losses_count:
        performance = "Improving 📈"
    elif losses_count > wins_count:
        performance = "Declining 📉"
    else:
        performance = "Stable ➖"

    return render(request, 'tournaments/team_detail.html', {
        'team': team,
        'memberships': memberships,
        'matches': matches,
        'trend': trend,
        'performance': performance,
    })


@login_required
def assign_coach(request, team_id):
    if not is_club_manager(request.user):
        return HttpResponseForbidden("Only Club Managers can assign coaches.")

    team = get_object_or_404(Team, id=team_id)

    if request.method == 'POST':
        form = AssignCoachForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            return redirect('team_detail', team_id=team.id)
    else:
        form = AssignCoachForm(instance=team)

    return render(request, 'tournaments/assign_coach.html', {
        'form': form,
        'team': team
    })


@login_required
def add_player(request, team_id):
    if not is_club_manager(request.user):
        return HttpResponseForbidden("Only Club Managers can add players.")

    team = get_object_or_404(Team, id=team_id)

    if request.method == 'POST':
        form = AddPlayerForm(request.POST, team=team)
        if form.is_valid():
            membership = form.save(commit=False)
            membership.team = team
            membership.save()
            return redirect('team_detail', team_id=team.id)
    else:
        form = AddPlayerForm(team=team)

    return render(request, 'tournaments/add_player.html', {
        'form': form,
        'team': team
    })


@login_required
def remove_player(request, team_id, membership_id):
    if not is_club_manager(request.user):
        return HttpResponseForbidden("Only Club Managers can remove players.")

    team = get_object_or_404(Team, id=team_id)
    membership = get_object_or_404(TeamMembership, id=membership_id, team=team)

    if request.method == 'POST':
        membership.delete()
        return redirect('team_detail', team_id=team.id)

    return render(request, 'tournaments/confirm_remove_player.html', {
        'team': team,
        'membership': membership,
    })


@login_required
def edit_match_time(request, match_id):
    if not is_club_manager(request.user):
        return HttpResponseForbidden("Only Club Managers can edit match times.")

    match = get_object_or_404(Match, id=match_id)

    if match.match_date < date.today():
        messages.error(request, "Cannot edit the time of a match that has already taken place.")
        return redirect('tournament_detail', tournament_id=match.tournament.id)

    if request.method == 'POST':
        form = EditMatchTimeForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
            messages.success(request, "Match time updated successfully.")
            return redirect('tournament_detail', tournament_id=match.tournament.id)
    else:
        form = EditMatchTimeForm(instance=match)

    return render(request, 'tournaments/edit_match_time.html', {
        'form': form,
        'match': match,
    })


@login_required
def update_match_venue(request, match_id):
    if not is_club_manager(request.user):
        return HttpResponseForbidden("Only Club Managers can update match venues.")

    match = get_object_or_404(Match, id=match_id)

    if match.match_date < date.today():
        messages.error(request, "Cannot update the venue of a match that has already taken place.")
        return redirect('tournament_detail', tournament_id=match.tournament.id)

    if request.method == 'POST':
        form = UpdateMatchVenueForm(request.POST, instance=match)
        if form.is_valid():
            updated_match = form.save()

            coach1 = updated_match.home_team.coach
            coach2 = updated_match.away_team.coach

            if coach1:
                Notification.objects.create(
                    user=coach1,
                    message=f"Venue updated for {updated_match.home_team.name} vs {updated_match.away_team.name}: {updated_match.venue}"
                )

            if coach2 and coach2 != coach1:
                Notification.objects.create(
                    user=coach2,
                    message=f"Venue updated for {updated_match.home_team.name} vs {updated_match.away_team.name}: {updated_match.venue}"
                )

            messages.success(request, "Match venue updated successfully.")
            return redirect('tournament_detail', tournament_id=updated_match.tournament.id)
    else:
        form = UpdateMatchVenueForm(instance=match)

    return render(request, 'tournaments/update_match_venue.html', {
        'form': form,
        'match': match,
    })


@login_required
def team_match_schedule(request, team_id):
    team = get_object_or_404(Team, id=team_id)

    if not is_coach(request.user) or team.coach != request.user:
        return HttpResponseForbidden("You can only view the schedule for your own team.")

    matches = Match.objects.filter(
        models.Q(home_team=team) | models.Q(away_team=team)
    ).select_related('tournament', 'home_team', 'away_team')

    return render(request, 'tournaments/team_match_schedule.html', {
        'team': team,
        'matches': matches,
    })


@login_required
def player_performance(request):
    if not is_player(request.user):
        return HttpResponseForbidden("Only players can view individual performance.")

    stats = PerformanceStat.objects.filter(
        player=request.user
    ).select_related('match', 'team').order_by('match__match_date', 'updated_at')

    totals = stats.aggregate(
        kills=Sum('kills'),
        assists=Sum('assists'),
        blocks=Sum('blocks'),
        digs=Sum('digs'),
        aces=Sum('aces'),
        errors=Sum('errors'),
    )

    return render(request, 'tournaments/player_performance.html', {
        'stats': stats,
        'totals': totals,
    })


@login_required
def team_performance(request, team_id):
    team = get_object_or_404(Team, id=team_id)

    if not is_coach(request.user) or team.coach != request.user:
        return HttpResponseForbidden("You can only view performance for your own team.")

    selected_period = request.GET.get('period', '')
    selected_metric = request.GET.get('metric', '')

    allowed_metrics = {
        'kills': 'Kills',
        'assists': 'Assists',
        'blocks': 'Blocks',
        'digs': 'Digs',
        'aces': 'Aces',
        'errors': 'Errors',
    }

    stats = PerformanceStat.objects.filter(team=team).select_related(
        'match',
        'player',
        'team'
    )

    if selected_period:
        stats = stats.filter(period=selected_period)

    totals = stats.aggregate(
        kills=Sum('kills'),
        assists=Sum('assists'),
        blocks=Sum('blocks'),
        digs=Sum('digs'),
        aces=Sum('aces'),
        errors=Sum('errors'),
    )

    metric_total = None
    selected_metric_label = None

    if selected_metric in allowed_metrics:
        metric_total = stats.aggregate(total=Sum(selected_metric))['total'] or 0
        selected_metric_label = allowed_metrics[selected_metric]

    stats = stats.order_by('match__match_date', 'updated_at')

    return render(request, 'tournaments/team_performance.html', {
        'team': team,
        'stats': stats,
        'totals': totals,
        'selected_period': selected_period,
        'selected_metric': selected_metric,
        'selected_metric_label': selected_metric_label,
        'metric_total': metric_total,
        'period_choices': PerformanceStat.PERIOD_CHOICES,
    })


@login_required
def generate_schedule(request, tournament_id):
    if not is_club_manager(request.user):
        return HttpResponseForbidden("Only Club Managers can generate schedules.")

    tournament = get_object_or_404(Tournament, id=tournament_id)
    teams = list(tournament.teams.all())

    if tournament.end_date < date.today():
        messages.error(request, "Cannot generate a schedule for a tournament that has already ended.")
        return redirect('tournament_detail', tournament_id=tournament.id)

    if len(teams) < 2:
        messages.error(request, "At least 2 teams are required to generate a schedule.")
        return redirect('tournament_detail', tournament_id=tournament.id)

    if tournament.matches.exists():
        messages.warning(request, "Schedule already exists for this tournament.")
        return redirect('tournament_detail', tournament_id=tournament.id)

    if tournament.format != 'round_robin':
        messages.error(request, "Automatic schedule generation is currently supported for round robin tournaments only.")
        return redirect('tournament_detail', tournament_id=tournament.id)

    current_date = tournament.start_date
    default_time = time(18, 0)
    default_venue = "Main Court"

    for i in range(len(teams)):
        for j in range(i + 1, len(teams)):
            Match.objects.create(
                tournament=tournament,
                home_team=teams[i],
                away_team=teams[j],
                match_date=current_date,
                match_time=default_time,
                venue=default_venue
            )

            current_date += timedelta(days=1)

            if current_date > tournament.end_date:
                current_date = tournament.start_date

    messages.success(request, "Tournament schedule generated successfully.")
    return redirect('tournament_detail', tournament_id=tournament.id)


@login_required
def update_match_score(request, match_id):
    if not is_coach(request.user):
        return HttpResponseForbidden("Only coaches can enter match scores.")

    match = get_object_or_404(Match, id=match_id)

    if match.home_team.coach != request.user and match.away_team.coach != request.user:
        return HttpResponseForbidden("You can only enter scores for matches involving your team.")

    if match.match_date > date.today():
        messages.error(request, "Cannot enter a score for a match that has not started yet.")
        return redirect('tournament_detail', tournament_id=match.tournament.id)

    if request.method == 'POST':
        form = MatchScoreForm(request.POST, instance=match)
        if form.is_valid():
            match = form.save()
            from .utils import update_standings
            update_standings(match.tournament)
            messages.success(request, "Match score updated successfully.")
            return redirect('tournament_detail', tournament_id=match.tournament.id)
    else:
        form = MatchScoreForm(instance=match)

    return render(request, 'tournaments/update_match_score.html', {
        'form': form,
        'match': match,
    })