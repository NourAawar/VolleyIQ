import math
from datetime import timedelta, time as default_time
from .models import Team, Match, Notification
from django.db.models import Sum
from .models import PerformanceStat


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
        team.points_for = 0
        team.points_against = 0

    for match in tournament.matches.select_related('home_team', 'away_team'):
        if match.home_score is None or match.away_score is None:
            continue
        home = teams.get(match.home_team_id)
        away = teams.get(match.away_team_id)
        if home is None or away is None:
            continue

        home.points_for += match.home_score
        home.points_against += match.away_score
        away.points_for += match.away_score
        away.points_against += match.home_score

        if match.home_score > match.away_score:
            home.wins += 1
            home.points += 3
            away.losses += 1
        elif match.away_score > match.home_score:
            away.wins += 1
            away.points += 3
            home.losses += 1

    Team.objects.bulk_update(
        list(teams.values()),
        ['wins', 'losses', 'points', 'points_for', 'points_against']
    )


def _next_power_of_two(n):
    return 2 ** math.ceil(math.log2(n)) if n > 1 else 1


def generate_single_elimination(tournament, teams, start_date):
    """Generate round 1 matches for a single elimination bracket."""
    n = len(teams)
    bracket_size = _next_power_of_two(n)
    byes = bracket_size - n

    # Top `byes` seeds advance automatically (no match in round 1)
    # Remaining teams play round 1
    playing_teams = teams[byes:]  # these teams actually play round 1
    bye_teams = teams[:byes]      # these teams skip to round 2

    match_date = start_date
    created = []
    for i in range(0, len(playing_teams), 2):
        Match.objects.create(
            tournament=tournament,
            home_team=playing_teams[i],
            away_team=playing_teams[i + 1],
            match_date=match_date,
            match_time=default_time(18, 0),
            venue='Main Court',
            round_number=1,
            bracket='winners',
        )
        created.append((playing_teams[i], playing_teams[i + 1]))
        match_date += timedelta(days=1)
        if match_date > tournament.end_date:
            match_date = start_date

    return bye_teams


def advance_single_elimination(tournament):
    """
    Look at the current highest completed round. If all matches are scored,
    generate the next round from winners (plus any stored byes).
    Returns True if a new round was created, False if already complete or not ready.
    """
    matches = list(
        tournament.matches
        .filter(bracket='winners')
        .select_related('home_team', 'away_team')
        .order_by('round_number')
    )
    if not matches:
        return False

    current_round = max(m.round_number for m in matches)
    round_matches = [m for m in matches if m.round_number == current_round]

    # Check all matches in the current round are scored
    if any(m.home_score is None or m.away_score is None for m in round_matches):
        return False

    # Collect winners
    winners = []
    for m in round_matches:
        if m.home_score > m.away_score:
            winners.append(m.home_team)
        elif m.away_score > m.home_score:
            winners.append(m.away_team)
        else:
            # Draw: home team advances (tournament rules should prevent this but handle gracefully)
            winners.append(m.home_team)

    if len(winners) == 1:
        return False  # Tournament is over

    next_round = current_round + 1
    match_date = tournament.start_date
    for i in range(0, len(winners), 2):
        if i + 1 >= len(winners):
            break
        Match.objects.create(
            tournament=tournament,
            home_team=winners[i],
            away_team=winners[i + 1],
            match_date=match_date,
            match_time=default_time(18, 0),
            venue='Main Court',
            round_number=next_round,
            bracket='winners',
        )
        match_date += timedelta(days=1)
        if match_date > tournament.end_date:
            match_date = tournament.start_date

    return True


def generate_double_elimination(tournament, teams, start_date):
    """Generate round 1 of the winners bracket for double elimination."""
    match_date = start_date
    for i in range(0, len(teams) - 1, 2):
        Match.objects.create(
            tournament=tournament,
            home_team=teams[i],
            away_team=teams[i + 1],
            match_date=match_date,
            match_time=default_time(18, 0),
            venue='Main Court',
            round_number=1,
            bracket='winners',
        )
        match_date += timedelta(days=1)
        if match_date > tournament.end_date:
            match_date = tournament.start_date

    # If odd team count, last team gets a bye (auto-advances, no round-1 match)


def advance_double_elimination(tournament):
    """
    After all current-round winners bracket matches are scored:
    - Generate next winners bracket round from winners
    - Move losers into the losers bracket
    - Generate losers bracket matches
    Returns True if anything was created.
    """
    all_matches = list(
        tournament.matches
        .select_related('home_team', 'away_team')
        .order_by('round_number')
    )

    winners_matches = [m for m in all_matches if m.bracket == 'winners']
    losers_matches = [m for m in all_matches if m.bracket == 'losers']

    if not winners_matches:
        return False

    current_w_round = max(m.round_number for m in winners_matches)
    current_w_matches = [m for m in winners_matches if m.round_number == current_w_round]

    if any(m.home_score is None or m.away_score is None for m in current_w_matches):
        return False

    match_date = tournament.start_date

    # Collect winners and losers from current winners bracket round
    w_winners, w_losers = [], []
    for m in current_w_matches:
        if m.home_score >= m.away_score:
            w_winners.append(m.home_team)
            w_losers.append(m.away_team)
        else:
            w_winners.append(m.away_team)
            w_losers.append(m.home_team)

    created = False

    # Generate next winners bracket round if more than 1 winner
    if len(w_winners) > 1:
        next_w_round = current_w_round + 1
        for i in range(0, len(w_winners) - 1, 2):
            Match.objects.create(
                tournament=tournament,
                home_team=w_winners[i],
                away_team=w_winners[i + 1],
                match_date=match_date,
                match_time=default_time(18, 0),
                venue='Main Court',
                round_number=next_w_round,
                bracket='winners',
            )
            match_date += timedelta(days=1)
            if match_date > tournament.end_date:
                match_date = tournament.start_date
        created = True

    # Handle losers bracket
    # Collect teams currently in losers bracket that haven't lost yet (survived losers matches)
    losers_survivors = []
    if losers_matches:
        current_l_round = max(m.round_number for m in losers_matches)
        current_l_matches = [m for m in losers_matches if m.round_number == current_l_round]
        if all(m.home_score is not None and m.away_score is not None for m in current_l_matches):
            for m in current_l_matches:
                if m.home_score >= m.away_score:
                    losers_survivors.append(m.home_team)
                else:
                    losers_survivors.append(m.away_team)

    # New losers bracket entrants = losers from this winners bracket round
    all_losers_bracket = w_losers + losers_survivors
    next_l_round = (max((m.round_number for m in losers_matches), default=0)) + 1

    if len(all_losers_bracket) >= 2:
        for i in range(0, len(all_losers_bracket) - 1, 2):
            Match.objects.create(
                tournament=tournament,
                home_team=all_losers_bracket[i],
                away_team=all_losers_bracket[i + 1],
                match_date=match_date,
                match_time=default_time(19, 0),
                venue='Main Court',
                round_number=next_l_round,
                bracket='losers',
            )
            match_date += timedelta(days=1)
            if match_date > tournament.end_date:
                match_date = tournament.start_date
        created = True

    # Check if it's time for the grand final
    # Grand final: 1 winner bracket survivor vs 1 losers bracket survivor
    if len(w_winners) == 1 and len(losers_survivors) == 1:
        if not any(m.bracket == 'grand_final' for m in all_matches):
            Match.objects.create(
                tournament=tournament,
                home_team=w_winners[0],
                away_team=losers_survivors[0],
                match_date=match_date,
                match_time=default_time(18, 0),
                venue='Main Court',
                round_number=current_w_round + 1,
                bracket='grand_final',
            )
            created = True

    return created

def get_player_recommendations(team):
    recommendations = {}

    wins = team.wins
    losses = team.losses
    total_matches = wins + losses

    for membership in team.memberships.select_related('player'):
        player = membership.player
        player_recs = []

        name = player.get_full_name() or player.username

        if total_matches == 0:
            player_recs.append(
                "Not enough match data yet to generate recommendations."
            )
            recommendations[name] = player_recs
            continue

        if losses > wins:
            player_recs.append("Focus on improving consistency during high-pressure matches.")

            if membership.position == "setter":
                player_recs.append("Improve ball distribution and decision-making.")
            elif membership.position == "libero":
                player_recs.append("Work on defensive positioning and reaction speed.")
            else:
                player_recs.append("Improve attacking accuracy and timing.")

        elif wins > losses:
            player_recs.append("Maintain performance and refine advanced skills.")

            if membership.position == "setter":
                player_recs.append("Enhance quick play strategies.")
            elif membership.position == "middle_blocker":
                player_recs.append("Improve blocking timing and reading opponents.")

        else:
            player_recs.append("Focus on teamwork coordination and communication.")

        recommendations[name] = player_recs

    return recommendations

from django.db.models import Sum
from .models import PerformanceStat

def get_coach_insights(team):
    insights = {}

    for membership in team.memberships.select_related('player'):
        player = membership.player
        stats = PerformanceStat.objects.filter(player=player)

        data = stats.aggregate(
            kills=Sum('kills'),
            assists=Sum('assists'),
            blocks=Sum('blocks'),
            digs=Sum('digs'),
            aces=Sum('aces'),
            errors=Sum('errors'),
        )

        for k in data:
            if data[k] is None:
                data[k] = 0

        player_insights = []

        total_matches = stats.count()

        if total_matches == 0:
            player_insights.append("No matches played yet.")
        else:
            matches = total_matches if total_matches > 0 else 1

            # Averages (more accurate than totals)
            avg_kills = (data['kills'] or 0) / matches
            avg_digs = (data['digs'] or 0) / matches
            avg_errors = (data['errors'] or 0) / matches

            # Attack insight
            if avg_kills >= 5:
                player_insights.append("Strong attacking performance.")
            elif avg_kills >= 2:
                player_insights.append("Decent attacking contribution.")
            else:
                player_insights.append("Low attacking output → needs improvement.")

            # Defense insight
            if avg_digs >= 4:
                player_insights.append("Good defensive contribution.")

            # Error insight (FIXED VERSION)
            if avg_errors >= 3:
                player_insights.append("High error rate → needs consistency training.")
            elif avg_errors >= 1.5:
                player_insights.append("Moderate error rate → needs improvement.")
            else:
                player_insights.append("Low error rate → solid consistency.")

            # Overall balance
            if (data['kills'] or 0) > (data['errors'] or 0):
                player_insights.append("Positive overall impact.")

        insights[player.username] = {
            "name": player.get_full_name() or player.username,
            "insights": player_insights
        }

    return insights