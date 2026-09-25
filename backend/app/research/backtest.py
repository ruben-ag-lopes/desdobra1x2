"""Walk-forward backtest of 1X2 models (and, with --goals, of the goal markets).

    python -m app.research.backtest --league P1 --seasons 8 --test-seasons 2
    python -m app.research.backtest --league P1 --goals

Models are refitted every `--refit-days` using only matches played before the
refit date, then predict the next block of matches. Metrics are computed on the
test period only, and bookmaker closing odds are shown as an external reference.
"""

import argparse
import json
from datetime import timedelta

import numpy as np

from app.research import metrics
from app.research.data import current_season_start, load_international, load_league
from app.research.features import build_rows
from app.research.models import PoissonModel, all_models
from app.storage import bigquery


def walk_forward(matches, rows, test_start, refit_days: int) -> dict[str, np.ndarray]:
    dates = np.array([m.date for m in matches])
    test_idx = np.where((dates >= test_start) & rows.eligible)[0]
    preds = {model.name: np.zeros((len(test_idx), 3)) for model in all_models()}

    block_start = test_start
    last_date = dates[-1]
    while block_start <= last_date:
        block_end = block_start + timedelta(days=refit_days)
        train = np.where((dates < block_start) & rows.eligible)[0]
        in_block = (dates[test_idx] >= block_start) & (dates[test_idx] < block_end)
        if in_block.any():
            test_rows = rows.subset(test_idx[in_block])
            for model in all_models():
                model.fit(rows.subset(train))
                preds[model.name][in_block] = model.predict(test_rows)
        block_start = block_end
    return {"_idx": test_idx, **preds}


GOAL_MARKETS = ("over25", "btts")


def goal_models() -> list[PoissonModel]:
    return [PoissonModel(), PoissonModel(use_h2h=True), PoissonModel(dixon_coles=True),
            PoissonModel(use_h2h=True, dixon_coles=True)]


def walk_forward_goals(matches, rows, test_start, refit_days: int) -> tuple[np.ndarray, dict]:
    """Same refit schedule as walk_forward; P(over 2.5) and P(both score) per model."""
    dates = np.array([m.date for m in matches])
    test_idx = np.where((dates >= test_start) & rows.eligible)[0]
    names = ["frequencias"] + [m.name for m in goal_models()]
    preds = {name: {k: np.zeros(len(test_idx)) for k in GOAL_MARKETS} for name in names}
    total = rows.home_goals + rows.away_goals
    observed = {"over25": (total >= 3).astype(float), "btts": ((rows.home_goals > 0) & (rows.away_goals > 0)).astype(float)}

    block_start = test_start
    while block_start <= dates[-1]:
        block_end = block_start + timedelta(days=refit_days)
        train = np.where((dates < block_start) & rows.eligible)[0]
        in_block = (dates[test_idx] >= block_start) & (dates[test_idx] < block_end)
        if in_block.any():
            test_rows = rows.subset(test_idx[in_block])
            for k in GOAL_MARKETS:
                preds["frequencias"][k][in_block] = observed[k][train].mean()
            for model in goal_models():
                model.fit(rows.subset(train))
                for k, p in model.goal_markets(test_rows).items():
                    preds[model.name][k][in_block] = p
        block_start = block_end
    return test_idx, {"preds": preds, "observed": {k: v[test_idx] for k, v in observed.items()}}


def bookmaker_over25(matches, idx) -> tuple[np.ndarray, np.ndarray]:
    """Margin-free implied P(over 2.5), and a mask of matches that have those odds."""
    out = np.zeros(len(idx))
    mask = np.zeros(len(idx), dtype=bool)
    for j, i in enumerate(idx):
        if matches[i].ou25_odds:
            over, under = 1 / np.array(matches[i].ou25_odds)
            out[j] = over / (over + under)
            mask[j] = True
    return out, mask


def print_goals(matches, rows, test_start, refit_days: int, label: str) -> dict:
    idx, result = walk_forward_goals(matches, rows, test_start, refit_days)
    print(f"Liga {label}: mercados de golos, teste desde {test_start:%Y-%m-%d} ({len(idx)} jogos)")
    summary = {}
    book, has_odds = bookmaker_over25(matches, idx)
    for k, title in (("over25", "Mais de 2,5 golos"), ("btts", "Ambas marcam")):
        y = result["observed"][k]
        print(f"\n{title} (ocorreu em {y.mean():.1%} dos jogos)")
        header = f"{'modelo':<28}{'log_loss':>10}{'brier':>9}{'ece':>8}"
        print(header)
        print("-" * len(header))
        for name, preds in result["preds"].items():
            s = metrics.binary_summary(preds[k], y)
            summary[f"{k}:{name}"] = s
            print(f"{name:<28}{s['log_loss']:>10.4f}{s['brier']:>9.4f}{s['ece']:>8.4f}")
        if k == "over25" and has_odds.any():
            s = metrics.binary_summary(book[has_odds], y[has_odds])
            summary["over25:casas_de_apostas"] = s
            print(f"{'casas_de_apostas (ref.)':<28}{s['log_loss']:>10.4f}{s['brier']:>9.4f}{s['ece']:>8.4f}")
    return summary


def bookmaker_probs(matches, idx) -> tuple[np.ndarray, np.ndarray]:
    """Margin-free implied probabilities, and a mask of matches that have odds."""
    out = np.zeros((len(idx), 3))
    mask = np.zeros(len(idx), dtype=bool)
    for j, i in enumerate(idx):
        if matches[i].odds:
            inv = 1 / np.array(matches[i].odds)
            out[j] = inv / inv.sum()
            mask[j] = True
    return out, mask


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--league", default="P1")
    parser.add_argument("--international", action="store_true", help="national teams instead of a league")
    parser.add_argument(
        "--last-season", type=int, default=current_season_start(), help="start year of the last season"
    )
    parser.add_argument("--seasons", type=int, default=8)
    parser.add_argument("--test-seasons", type=int, default=2)
    parser.add_argument("--refit-days", type=int, default=28)
    parser.add_argument("--calibration", action="store_true", help="print calibration tables")
    parser.add_argument("--goals", action="store_true", help="backtest the goal markets (over 2.5, both score)")
    parser.add_argument("--json", help="write results to this file")
    parser.add_argument("--bigquery", action="store_true", help="store every test prediction (needs GCP_PROJECT/BQ_DATASET)")
    args = parser.parse_args()

    if args.international:
        matches = load_international(since_year=args.last_season - args.seasons)
        rows = build_rows(matches, k=40.0, home_adv=100.0, season_regress=0.0)
        args.league = "seleções"
    else:
        matches = load_league(args.league, args.last_season, args.seasons)
        rows = build_rows(matches)
    first_test_year = args.last_season - args.test_seasons + 1
    test_start = next(m.date for m in matches if m.date.year >= first_test_year and m.date.month >= 7)

    if args.goals:
        summary = print_goals(matches, rows, test_start, args.refit_days, args.league)
        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
        return

    result = walk_forward(matches, rows, test_start, args.refit_days)
    idx = result.pop("_idx")
    y = rows.outcome[idx]
    book, has_odds = bookmaker_probs(matches, idx)

    print(f"Liga {args.league}: {len(matches)} jogos, teste desde {test_start:%Y-%m-%d} ({len(idx)} jogos)\n")
    header = f"{'modelo':<28}{'log_loss':>10}{'rps':>9}{'brier':>9}{'ece':>8}"
    print(header)
    print("-" * len(header))
    summary = {}
    for name, probs in result.items():
        s = metrics.summarize(probs, y)
        summary[name] = s
        print(f"{name:<28}{s['log_loss']:>10.4f}{s['rps']:>9.4f}{s['brier']:>9.4f}{s['ece']:>8.4f}")
    if has_odds.any():
        s = metrics.summarize(book[has_odds], y[has_odds])
        summary["casas_de_apostas (ref.)"] = s
        print(f"{'casas_de_apostas (ref.)':<28}{s['log_loss']:>10.4f}{s['rps']:>9.4f}{s['brier']:>9.4f}{s['ece']:>8.4f}")

    if args.calibration:
        for name, probs in result.items():
            print(f"\nCalibração — {name}")
            for r in metrics.calibration_table(probs, y):
                print(f"  {r['outcome']} {r['bin']}  n={r['n']:>4}  previsto={r['predicted']:.3f}  observado={r['observed']:.3f}")

    if args.bigquery:
        if not bigquery.enabled():
            print("\nBigQuery: define GCP_PROJECT e BQ_DATASET para guardar as previsões.")
        else:
            run_id = bigquery.log_backtest(args.league, matches, result, idx)
            print(f"\nBigQuery: previsões guardadas (run_id={run_id})")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
