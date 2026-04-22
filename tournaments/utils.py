from .models import Team

def update_standings(tournament):
    teams = tournament.teams.all()

    # reset stats
    for team in teams:
        team.wins = 0
        team.losses = 0
        team.points = 0
        team.save()

    matches = tournament.matches.all()

    for match in matches:
        if match.home_score is None or match.away_score is None:
            continue

        home = match.home_team
        away = match.away_team

        if match.home_score > match.away_score:
            home.wins += 1
            home.points += 3
            away.losses += 1

        elif match.away_score > match.home_score:
            away.wins += 1
            away.points += 3
            home.losses += 1

        home.save()
        away.save()