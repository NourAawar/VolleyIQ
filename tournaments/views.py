from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import (
    TournamentForm, TeamForm, AssignCoachForm, AddPlayerForm,
    RegisterTeamForm, EditMatchTimeForm, UpdateMatchVenueForm,
    MatchScoreForm, AssignTaskForm, PlayerAvailabilityForm, AttendanceForm,
    RegistrationForm, TeamMessageForm
)
from .models import Tournament, Team, TeamMembership, Match, Notification, PerformanceStat, Task, PlayerAvailability, Attendance, Announcement
from django.forms import modelformset_factory
from .utils import (
    update_standings, notify_match_coaches,
    generate_single_elimination, advance_single_elimination,
    generate_double_elimination, advance_double_elimination,
)
from django.contrib import messages
from datetime import timedelta, time, date
from django.db import models
from django.db.models import Sum, F


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


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created! You can now log in.")
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


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
        tournament_name = tournament.name
        tournament.delete()
        messages.success(request, f"Tournament '{tournament_name}' has been deleted.")
        return redirect('tournament_list')

    return render(request, 'tournaments/confirm_delete_tournament.html', {
        'tournament': tournament,
    })


@login_required
def tournament_list(request):
    tournaments = Tournament.objects.all()
    return render(request, 'tournaments/tournament_list.html', {
        'tournaments': tournaments,
        'today': date.today(),
    })


@login_required
def tournament_detail(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)

    registered_teams = tournament.teams.annotate(
        point_diff=F('points_for') - F('points_against')
    ).order_by('-points', '-wins', '-point_diff')

    matches = tournament.matches.select_related(
        'home_team',
        'away_team',
        'home_team__coach',
        'away_team__coach',
    )

    return render(request, 'tournaments/tournament_detail.html', {
        'tournament': tournament,
        'registered_teams': registered_teams,
        'matches': matches,
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

    match = get_object_or_404(Match.objects.select_related('tournament'), id=match_id)

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

    match = get_object_or_404(
        Match.objects.select_related('tournament', 'home_team__coach', 'away_team__coach'),
        id=match_id
    )

    if match.match_date < date.today():
        messages.error(request, "Cannot update the venue of a match that has already taken place.")
        return redirect('tournament_detail', tournament_id=match.tournament.id)

    if request.method == 'POST':
        form = UpdateMatchVenueForm(request.POST, instance=match)
        if form.is_valid():
            updated_match = form.save()
            notify_match_coaches(
                updated_match,
                f"Venue updated for {updated_match.home_team.name} vs {updated_match.away_team.name}: {updated_match.venue}"
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

    fmt = tournament.format

    if fmt == 'round_robin':
        current_date = tournament.start_date
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                Match.objects.create(
                    tournament=tournament,
                    home_team=teams[i],
                    away_team=teams[j],
                    match_date=current_date,
                    match_time=time(18, 0),
                    venue='Main Court',
                )
                current_date += timedelta(days=1)
                if current_date > tournament.end_date:
                    current_date = tournament.start_date

    elif fmt == 'single_elimination':
        if len(teams) < 2:
            messages.error(request, "At least 2 teams required for elimination.")
            return redirect('tournament_detail', tournament_id=tournament.id)
        generate_single_elimination(tournament, teams, tournament.start_date)

    elif fmt == 'double_elimination':
        if len(teams) < 2:
            messages.error(request, "At least 2 teams required for elimination.")
            return redirect('tournament_detail', tournament_id=tournament.id)
        generate_double_elimination(tournament, teams, tournament.start_date)

    else:
        messages.error(request, "Unknown tournament format.")
        return redirect('tournament_detail', tournament_id=tournament.id)

    # Notify all team coaches in this tournament
    notified = set()
    for team in teams:
        if team.coach and team.coach.id not in notified:
            Notification.objects.create(
                user=team.coach,
                message=f"Match schedule has been generated for tournament: {tournament.name}"
            )
            notified.add(team.coach.id)

    messages.success(request, "Tournament schedule generated successfully.")
    return redirect('tournament_detail', tournament_id=tournament.id)


@login_required
def advance_round(request, tournament_id):
    if not is_club_manager(request.user):
        return HttpResponseForbidden("Only Club Managers can advance rounds.")

    tournament = get_object_or_404(Tournament, id=tournament_id)

    if tournament.format == 'single_elimination':
        created = advance_single_elimination(tournament)
    elif tournament.format == 'double_elimination':
        created = advance_double_elimination(tournament)
    else:
        messages.error(request, "Round advancement is only for elimination formats.")
        return redirect('tournament_detail', tournament_id=tournament.id)

    if created:
        messages.success(request, "Next round generated successfully.")
    else:
        current_matches = tournament.matches.filter(bracket__in=['winners', 'grand_final'])
        unscored = current_matches.filter(home_score__isnull=True)
        if unscored.exists():
            messages.warning(request, "All matches in the current round must be scored before advancing.")
        else:
            messages.info(request, "The tournament is complete — no further rounds to generate.")

    return redirect('tournament_detail', tournament_id=tournament.id)


@login_required
def update_match_score(request, match_id):
    if not is_coach(request.user):
        return HttpResponseForbidden("Only coaches can enter match scores.")

    match = get_object_or_404(
        Match.objects.select_related('home_team__coach', 'away_team__coach', 'tournament'),
        id=match_id
    )

    if match.home_team.coach != request.user and match.away_team.coach != request.user:
        return HttpResponseForbidden("You can only enter scores for matches involving your team.")

    if match.match_date > date.today():
        messages.error(request, "Cannot enter a score for a match that has not started yet.")
        return redirect('tournament_detail', tournament_id=match.tournament.id)

    if request.method == 'POST':
        form = MatchScoreForm(request.POST, instance=match)
        if form.is_valid():
            match = form.save()
            update_standings(match.tournament)
            notify_match_coaches(
                match,
                f"Score recorded: {match.home_team.name} {match.home_score} - {match.away_score} {match.away_team.name}"
            )
            messages.success(request, "Match score updated successfully.")
            return redirect('tournament_detail', tournament_id=match.tournament.id)
    else:
        form = MatchScoreForm(instance=match)

    return render(request, 'tournaments/update_match_score.html', {
        'form': form,
        'match': match,
    })


@login_required
def assign_task(request, team_id):
    if not is_coach(request.user):
        return HttpResponseForbidden("Only coaches can assign tasks.")

    team = get_object_or_404(Team, id=team_id)

    if team.coach != request.user:
        return HttpResponseForbidden("You can only assign tasks to players on your own team.")

    if request.method == 'POST':
        form = AssignTaskForm(request.POST, team=team)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user
            task.team = team
            task.save()
            Notification.objects.create(
                user=task.assigned_to,
                message=f"New task assigned by {request.user.username}: {task.title}"
            )
            messages.success(request, "Task assigned successfully.")
            return redirect('team_tasks', team_id=team.id)
    else:
        form = AssignTaskForm(team=team)

    return render(request, 'tournaments/assign_task.html', {
        'form': form,
        'team': team,
    })


@login_required
def team_tasks(request, team_id):
    if not is_coach(request.user):
        return HttpResponseForbidden("Only coaches can view team tasks.")

    team = get_object_or_404(Team, id=team_id)

    if team.coach != request.user:
        return HttpResponseForbidden("You can only view tasks for your own team.")

    tasks = Task.objects.filter(team=team).select_related('assigned_to', 'assigned_by')

    return render(request, 'tournaments/team_tasks.html', {
        'team': team,
        'tasks': tasks,
    })


@login_required
def my_tasks(request):
    if not is_player(request.user):
        return HttpResponseForbidden("Only players can view their tasks.")

    tasks = Task.objects.filter(assigned_to=request.user).select_related('team', 'assigned_by')

    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        new_status = request.POST.get('status')
        allowed_statuses = [s for s, _ in Task.STATUS_CHOICES]
        if task_id and new_status in allowed_statuses:
            Task.objects.filter(id=task_id, assigned_to=request.user).update(status=new_status)
        return redirect('my_tasks')

    return render(request, 'tournaments/my_tasks.html', {
        'tasks': tasks,
        'status_choices': Task.STATUS_CHOICES,
    })


@login_required
def match_availability(request, match_id):
    match = get_object_or_404(
        Match.objects.select_related('home_team__coach', 'away_team__coach', 'tournament'),
        id=match_id
    )

    if is_coach(request.user):
        if match.home_team.coach == request.user:
            team = match.home_team
        elif match.away_team.coach == request.user:
            team = match.away_team
        else:
            return HttpResponseForbidden("You can only view availability for your own team's matches.")
        player_ids = list(team.memberships.values_list('player_id', flat=True))
    elif is_club_manager(request.user):
        team = None
        player_ids = list(match.home_team.memberships.values_list('player_id', flat=True)) + \
                     list(match.away_team.memberships.values_list('player_id', flat=True))
    else:
        return HttpResponseForbidden("Only coaches and club managers can view player availability.")

    for pid in player_ids:
        PlayerAvailability.objects.get_or_create(
            player_id=pid,
            match=match,
            defaults={'status': 'uncertain', 'updated_by': request.user}
        )

    AvailabilityFormSet = modelformset_factory(PlayerAvailability, form=PlayerAvailabilityForm, extra=0)
    queryset = PlayerAvailability.objects.filter(
        match=match,
        player_id__in=player_ids
    ).select_related('player')

    if request.method == 'POST':
        formset = AvailabilityFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.updated_by = request.user
                instance.save()
            messages.success(request, "Player availability updated.")
            return redirect('match_availability', match_id=match.id)
    else:
        formset = AvailabilityFormSet(queryset=queryset)

    return render(request, 'tournaments/match_availability.html', {
        'formset': formset,
        'match': match,
        'team': team,
    })


@login_required
def record_attendance(request, match_id):
    if not is_coach(request.user):
        return HttpResponseForbidden("Only coaches can record attendance.")

    match = get_object_or_404(
        Match.objects.select_related('home_team__coach', 'away_team__coach', 'tournament'),
        id=match_id
    )

    if match.home_team.coach == request.user:
        team = match.home_team
    elif match.away_team.coach == request.user:
        team = match.away_team
    else:
        return HttpResponseForbidden("You can only record attendance for your own team's matches.")

    if match.match_date > date.today():
        messages.error(request, "Cannot record attendance for a match that has not started yet.")
        return redirect('tournament_detail', tournament_id=match.tournament.id)

    player_ids = list(team.memberships.values_list('player_id', flat=True))

    for pid in player_ids:
        Attendance.objects.get_or_create(
            player_id=pid,
            match=match,
            defaults={'status': 'present', 'recorded_by': request.user}
        )

    AttendanceFormSet = modelformset_factory(Attendance, form=AttendanceForm, extra=0)
    queryset = Attendance.objects.filter(
        match=match,
        player_id__in=player_ids
    ).select_related('player')

    if request.method == 'POST':
        formset = AttendanceFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.recorded_by = request.user
                instance.save()
            messages.success(request, "Attendance recorded successfully.")
            return redirect('tournament_detail', tournament_id=match.tournament.id)
    else:
        formset = AttendanceFormSet(queryset=queryset)

    return render(request, 'tournaments/record_attendance.html', {
        'formset': formset,
        'match': match,
        'team': team,
    })

@login_required
def send_team_message(request, team_id):
    if not is_coach(request.user):
        return HttpResponseForbidden("Only coaches can send team messages.")

    team = get_object_or_404(Team, id = team_id) 

    if team.coach != request.user: 
        return HttpResponseForbidden("You can only send messages to your own team.")

    if request.method == 'POST': 
        form = TeamMessageForm(request.POST)

        if form.is_valid(): 
            announcement = form.save(commit = False) 
            announcement.sender = request.user  
            announcement.team = team 
            announcement.save() 
            player_ids = team.memberships.values_list('player_id', flat = True) 

            for pid in player_ids:
                Notification.objects.create( 
                    user_id = pid, 
                    message = f"New message from coach {request.user.username}: {announcement.title}" 
                ) 
                
            messages.success(request, "Message sent to team successfully.") 

            return redirect('team_detail', team_id = team.id) 
        
    else:
        form = TeamMessageForm() 

    return render(request, 'tournaments/send_team_message.html', {
        'form': form,
        'team': team,
    })