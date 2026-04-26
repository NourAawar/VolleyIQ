from .models import Team, Notification


def notify_match_coaches(match, message):
    coach1 = match.home_team.coach
    coach2 = match.away_team.coach
    if coach1:
        Notification.objects.create(user=coach1, message=message)
    if coach2 and coach2 != coach1:
        Notification.objects.create(user=coach2, message=message)


def update_standings(tournament):
    teams = {t.id: t for t in tournament.teams.all()}
    for team in teams.values():
        team.wins = 0
        team.losses = 0
        team.points = 0

    for match in tournament.matches.select_related('home_team', 'away_team'):
        if match.home_score is None or match.away_score is None:
            continue
        home = teams.get(match.home_team_id)
        away = teams.get(match.away_team_id)
        if home is None or away is None:
            continue
        if match.home_score > match.away_score:
            home.wins += 1
            home.points += 3
            away.losses += 1
        elif match.away_score > match.home_score:
            away.wins += 1
            away.points += 3
            home.losses += 1

    Team.objects.bulk_update(list(teams.values()), ['wins', 'losses', 'points'])