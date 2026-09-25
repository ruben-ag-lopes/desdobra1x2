from typing import Literal

from app.models import MatchInput, ResultProbabilities
from app.scrapers import elo_ratings, loaned_venues, team_stats, uefa_ranking
from app.scrapers.team_stats import TeamStatsUnavailable
from app.services import trained_model
from app.services.elo_formula import ELO_HOME_ADVANTAGE, elo_1x2

Outcome = Literal["1", "X", "2"]

# Criteria weights (sum to 1.0). "last2_in_competition" is redistributed
# proportionally across the other criteria when fewer than 2 games are available.
WEIGHT_RECENT_FORM = 0.40
WEIGHT_UEFA_RANKING = 0.30
WEIGHT_LAST2_COMPETITION = 0.15
WEIGHT_H2H = 0.10
WEIGHT_DOMESTIC_STANDING = 0.05
HOME_ADVANTAGE_BONUS = 0.10


def _form_score(results: list[Literal["W", "D", "L"]]) -> float:
    """0..1 score from a list of recent results, most recent first, recency-weighted."""
    if not results:
        return 0.5
    points = {"W": 1.0, "D": 0.5, "L": 0.0}
    weights = [1.0 / (i + 1) for i in range(len(results))]
    total_weight = sum(weights)
    return sum(points[r] * w for r, w in zip(results, weights)) / total_weight


def _standing_score(position: int | None, total_teams: int | None) -> float:
    if position is None or not total_teams or total_teams <= 1:
        return 0.5
    return 1.0 - (position - 1) / (total_teams - 1)


def _h2h_score(results_from_home_perspective: list[Outcome]) -> float:
    if not results_from_home_perspective:
        return 0.5
    points = {"1": 1.0, "X": 0.5, "2": 0.0}
    return sum(points[r] for r in results_from_home_perspective) / len(results_from_home_perspective)


def _fetch_or_manual_team_strength(match: MatchInput, is_home: bool) -> tuple[float, float, float, dict]:
    """Returns (form_score, last2_score, standing_score, breakdown) for one side of the match."""
    team_name = match.home_team if is_home else match.away_team
    manual = match.manual_home_stats if is_home else match.manual_away_stats

    recent_form: list = []
    last2: list = []
    position, total_teams = None, None

    used_manual = False
    if match.competition_code:
        try:
            team_id = team_stats.find_team_id(team_name)
            if team_id:
                recent_form = team_stats.get_recent_results(team_id, None, limit=5)
                last2 = team_stats.get_recent_results(team_id, match.competition_code, limit=2)
                position = team_stats.get_domestic_standing(team_id, match.competition_code)
        except TeamStatsUnavailable:
            used_manual = True
    else:
        used_manual = True

    if (not recent_form or position is None) and manual:
        used_manual = True
        recent_form = recent_form or manual.recent_form
        last2 = last2 or manual.last2_in_competition
        position = position if position is not None else manual.domestic_position
        total_teams = manual.domestic_total_teams

    form = _form_score(recent_form)
    last2_score = _form_score(last2) if last2 else None
    standing = _standing_score(position, total_teams)

    breakdown = {
        "recent_form": form,
        "last2_in_competition": last2_score if last2_score is not None else "ignored (<2 games)",
        "domestic_standing": standing,
        "source": "manual" if used_manual else "football-data.org",
    }
    return form, last2_score, standing, breakdown


def _elo_probabilities(match: MatchInput) -> ResultProbabilities | None:
    """1/X/2 probabilities from Elo ratings, or None when either team is unknown."""
    home_elo = elo_ratings.get_elo(match.home_team)
    away_elo = elo_ratings.get_elo(match.away_team)
    if home_elo is None or away_elo is None:
        return None

    is_loaned = match.home_is_loaned_venue
    if is_loaned is None:
        is_loaned = loaned_venues.plays_at_loaned_venue(match.home_team)
    dr = home_elo - away_elo + (0 if is_loaned else ELO_HOME_ADVANTAGE)

    prob_home, prob_draw, prob_away = elo_1x2(dr)

    return ResultProbabilities(
        match_id=match.id,
        home_team=match.home_team,
        away_team=match.away_team,
        prob_home=round(prob_home, 4),
        prob_draw=round(prob_draw, 4),
        prob_away=round(prob_away, 4),
        criteria_breakdown={
            "home": {"elo": round(home_elo), "source": "elo"},
            "away": {"elo": round(away_elo), "source": "elo"},
        },
        modelo="elo-direto-v1",
    )


def _trained_probabilities(match: MatchInput, result) -> ResultProbabilities | None:
    if result is None:
        return None
    (prob_home, prob_draw, prob_away), version = result
    return ResultProbabilities(
        match_id=match.id,
        home_team=match.home_team,
        away_team=match.away_team,
        prob_home=round(prob_home, 4),
        prob_draw=round(prob_draw, 4),
        prob_away=round(prob_away, 4),
        criteria_breakdown={},
        modelo=version,
    )


def calcular_probabilidades_lote(
    matches: list[MatchInput], criteria_multipliers: dict[str, float] | None = None
) -> list[ResultProbabilities]:
    """Best available model per match: trained on history, then live Elo, then the manual criteria.

    Args:
        matches: fixtures to predict.
        criteria_multipliers: per-criterion multipliers [0, 2]. Only applied to trained models.
    """
    trained = trained_model.predict_many([(m.home_team, m.away_team) for m in matches], criteria_multipliers)
    return [_trained_probabilities(m, t) or calcular_probabilidades(m) for m, t in zip(matches, trained)]


def calcular_probabilidades(match: MatchInput) -> ResultProbabilities:
    """Fallback chain without the trained model (live Elo, then the manual criteria).

    Note: criteria_multipliers only apply to trained models; they are ignored here.
    """

    elo_result = _elo_probabilities(match)
    if elo_result is not None:
        return elo_result

    home_form, home_last2, home_standing, home_breakdown = _fetch_or_manual_team_strength(match, is_home=True)
    away_form, away_last2, away_standing, away_breakdown = _fetch_or_manual_team_strength(match, is_home=False)

    home_uefa = uefa_ranking.rank_to_score(uefa_ranking.get_rank(match.home_country))
    away_uefa = uefa_ranking.rank_to_score(uefa_ranking.get_rank(match.away_country))

    h2h_score = _h2h_score(match.manual_h2h)

    weight_last2 = WEIGHT_LAST2_COMPETITION
    other_weight_total = WEIGHT_RECENT_FORM + WEIGHT_UEFA_RANKING + WEIGHT_H2H + WEIGHT_DOMESTIC_STANDING
    if home_last2 is None or away_last2 is None:
        redistribution = weight_last2 / other_weight_total
        weight_last2 = 0.0
    else:
        redistribution = 0.0

    w_form = WEIGHT_RECENT_FORM * (1 + redistribution)
    w_uefa = WEIGHT_UEFA_RANKING * (1 + redistribution)
    w_h2h = WEIGHT_H2H * (1 + redistribution)
    w_standing = WEIGHT_DOMESTIC_STANDING * (1 + redistribution)

    home_last2_val = home_last2 if home_last2 is not None else 0.5
    away_last2_val = away_last2 if away_last2 is not None else 0.5

    home_strength = (
        w_form * home_form
        + w_uefa * home_uefa
        + weight_last2 * home_last2_val
        + w_h2h * h2h_score
        + w_standing * home_standing
    )
    away_strength = (
        w_form * away_form
        + w_uefa * away_uefa
        + weight_last2 * away_last2_val
        + w_h2h * (1 - h2h_score)
        + w_standing * away_standing
    )

    is_loaned = match.home_is_loaned_venue
    if is_loaned is None:
        is_loaned = loaned_venues.plays_at_loaned_venue(match.home_team)
    if not is_loaned:
        home_strength += HOME_ADVANTAGE_BONUS

    # Draw likelihood: higher when the two strengths are close.
    diff = abs(home_strength - away_strength)
    draw_strength = max(0.15, 0.5 - diff)

    total = home_strength + away_strength + draw_strength
    prob_home = home_strength / total
    prob_draw = draw_strength / total
    prob_away = away_strength / total

    return ResultProbabilities(
        match_id=match.id,
        home_team=match.home_team,
        away_team=match.away_team,
        prob_home=round(prob_home, 4),
        prob_draw=round(prob_draw, 4),
        prob_away=round(prob_away, 4),
        criteria_breakdown={"home": home_breakdown, "away": away_breakdown},
        modelo="criterios-v0",
        low_confidence=True,
    )


def _allocate_counts(probs: dict[Outcome, float], n: int) -> dict[Outcome, int]:
    """Largest-remainder allocation of n bets across 1/X/2, with a floor rule:
    no outcome below 50% probability may end up as the sole/majority pick.
    """
    ordered: list[Outcome] = sorted(probs.keys(), key=lambda o: probs[o], reverse=True)
    top = ordered[0]

    if probs[top] < 0.5 and n >= 2:
        # Spread more evenly: guarantee at least 2 outcomes get bets.
        raw = {o: probs[o] * n for o in ordered}
        counts = {o: max(1, int(raw[o])) for o in ordered[:2]}
        counts[ordered[2]] = 0
        remaining = n - sum(counts.values())
        i = 0
        while remaining > 0:
            counts[ordered[i % 2]] += 1
            remaining -= 1
            i += 1
        return counts

    raw = {o: probs[o] * n for o in ordered}
    counts = {o: int(raw[o]) for o in ordered}
    remainder = n - sum(counts.values())
    fractional = sorted(ordered, key=lambda o: raw[o] - counts[o], reverse=True)
    for o in fractional[:remainder]:
        counts[o] += 1
    return counts


def _fixed_probabilities(match: MatchInput) -> ResultProbabilities:
    """Result locked by the user: no prediction, the chosen outcome in every bet."""
    (fixed,) = match.fixed_results
    return ResultProbabilities(
        match_id=match.id,
        home_team=match.home_team,
        away_team=match.away_team,
        prob_home=1.0 if fixed == "1" else 0.0,
        prob_draw=1.0 if fixed == "X" else 0.0,
        prob_away=1.0 if fixed == "2" else 0.0,
        criteria_breakdown={},
        fixed_results=[fixed],
        modelo="fixo",
    )


def _apply_double(p: ResultProbabilities, chosen: list[Outcome]) -> ResultProbabilities:
    """Keep the model's 1/X/2, then share the excluded outcome's probability between the two
    chosen ones in proportion to their own probabilities."""
    model = {"1": p.prob_home, "X": p.prob_draw, "2": p.prob_away}
    kept = sum(model[o] for o in chosen)
    share = {o: (model[o] / kept if kept > 0 else 0.5) if o in chosen else 0.0 for o in model}
    return p.model_copy(
        update={
            "prob_home": round(share["1"], 4),
            "prob_draw": round(share["X"], 4),
            "prob_away": round(share["2"], 4),
            "fixed_results": list(chosen),
            "probs_modelo": [p.prob_home, p.prob_draw, p.prob_away],
        }
    )


def _double_counts(probs: dict[Outcome, float], chosen: list[Outcome], n: int) -> dict[Outcome, int]:
    """Split n bets between the two chosen outcomes; both appear at least once when n >= 2."""
    counts = _allocate_counts(probs, n)
    if n >= 2:
        low, high = sorted(chosen, key=lambda o: counts[o])
        if counts[low] == 0:
            counts[low], counts[high] = 1, counts[high] - 1
    return counts


def gerar_desdobramento(
    matches: list[MatchInput], n_apostas: int, criteria_multipliers: dict[str, float] | None = None
) -> tuple[list[ResultProbabilities], list[list[Outcome]]]:
    """Generate spread of bets for the given matches.

    Args:
        matches: fixtures with optional fixed_results and manual stats.
        n_apostas: number of bet variants to generate.
        criteria_multipliers: per-criterion multipliers [0, 2], e.g., {"elo": 1.5, "casa": 0.8}.
                             Only applied to trained models.
    """
    to_predict = [m for m in matches if len(m.fixed_results) != 1]
    predicted = dict(
        zip((m.id for m in to_predict), calcular_probabilidades_lote(to_predict, criteria_multipliers))
    )

    probabilities: list[ResultProbabilities] = []
    for m in matches:
        if len(m.fixed_results) == 1:
            probabilities.append(_fixed_probabilities(m))
        elif len(m.fixed_results) == 2:
            probabilities.append(_apply_double(predicted[m.id], m.fixed_results))
        else:
            probabilities.append(predicted[m.id])

    per_match_sequences: list[list[Outcome]] = []
    for idx, p in enumerate(probabilities):
        if len(p.fixed_results) == 1:
            per_match_sequences.append([p.fixed_results[0]] * n_apostas)
            continue
        probs: dict[Outcome, float] = {"1": p.prob_home, "X": p.prob_draw, "2": p.prob_away}
        if len(p.fixed_results) == 2:
            counts = _double_counts(probs, p.fixed_results, n_apostas)
        else:
            counts = _allocate_counts(probs, n_apostas)

        sequence: list[Outcome] = []
        for outcome in ("1", "X", "2"):
            sequence.extend([outcome] * counts[outcome])
        sequence = sequence[:n_apostas]
        while len(sequence) < n_apostas:
            sequence.append(sequence[-1] if sequence else "1")

        # Decorrelate each match's sequence so coupons differ across the coupon set.
        offset = (idx * 7 + 3) % max(n_apostas, 1)
        sequence = sequence[offset:] + sequence[:offset]
        per_match_sequences.append(sequence)

    apostas: list[list[Outcome]] = []
    for i in range(n_apostas):
        apostas.append([seq[i] for seq in per_match_sequences])

    return probabilities, apostas
