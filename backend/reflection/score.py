"""Deterministic scoring for a single completed UFC fight. Pure Python — no
LLM, no network calls. Fully unit-testable.

Inputs:
- predicted: dict from analyses.json `bets` block, normalized to top-level
  {winner, win_prob, method, rounds} where method has ko_tko/submission/decision
  and rounds has ends_round_1..ends_round_4_or_later + goes_to_decision.
- actual: dict from outcome_scraper {winner, method, round, time, stats}.
  method is one of "KO/TKO", "Submission", "Decision". round=None for decisions.
- closing_line: dict {f1_moneyline, f1_implied_prob} or None.

Outputs the `scoring` block defined in the spec.
"""

from __future__ import annotations

import math
from typing import Any

EDGE_THRESHOLD = 0.05  # |our_prob - closing_implied| <= this -> "pass"


def _predicted_method(predicted: dict) -> str:
    """Return the method label with the highest probability."""
    methods = predicted.get("method", {})
    if not methods:
        return "Decision"
    labels = {"ko_tko": "KO/TKO", "submission": "Submission", "decision": "Decision"}
    best_key = max(methods, key=methods.get)
    return labels.get(best_key, "Decision")


def _predicted_round(predicted: dict) -> str:
    """Return 'decision' or 'R<n>' for the highest-prob round bucket."""
    rounds = predicted.get("rounds", {})
    if not rounds:
        return "decision"
    candidates = {
        "decision": rounds.get("goes_to_decision", 0.0),
        "R1": rounds.get("ends_round_1", 0.0),
        "R2": rounds.get("ends_round_2", 0.0),
        "R3": rounds.get("ends_round_3", 0.0),
        "R4+": rounds.get("ends_round_4_or_later", 0.0),
    }
    return max(candidates, key=candidates.get)


def _actual_round_bucket(actual: dict) -> str:
    """Map actual outcome to the same bucket scheme as _predicted_round."""
    if actual.get("method", "").lower() == "decision":
        return "decision"
    r = actual.get("round")
    if r == 1:
        return "R1"
    if r == 2:
        return "R2"
    if r == 3:
        return "R3"
    if isinstance(r, int) and r >= 4:
        return "R4+"
    return "decision"  # fallback for missing data


def _we_said_f1_prob(predicted: dict, fighter1: str) -> float:
    """Normalize our prediction to fighter1's win probability."""
    if predicted.get("winner") == fighter1:
        return float(predicted.get("win_prob", 0.5))
    return 1.0 - float(predicted.get("win_prob", 0.5))


def _moneyline_payout(implied_prob: float) -> float:
    """$100 unit at the given implied probability — profit if it wins."""
    if implied_prob <= 0 or implied_prob >= 1:
        return 0.0
    return 100.0 * (1.0 - implied_prob) / implied_prob


def score_fight(
    fighter1: str,
    fighter2: str,
    predicted: dict,
    actual: dict,
    closing_line: dict | None,
) -> dict[str, Any]:
    """Compute the per-fight scoring block."""
    pick_correct = predicted.get("winner") == actual.get("winner")

    # Brier score is relative to fighter1's outcome (binary).
    we_said_f1 = _we_said_f1_prob(predicted, fighter1)
    f1_won = 1.0 if actual.get("winner") == fighter1 else 0.0
    brier = (we_said_f1 - f1_won) ** 2

    # Log loss: penalize confident-wrong harder. Clip to avoid log(0).
    p = max(0.001, min(0.999, we_said_f1 if f1_won else 1.0 - we_said_f1))
    log_loss = -math.log(p)

    method_correct = _predicted_method(predicted) == actual.get("method")
    round_correct = _predicted_round(predicted) == _actual_round_bucket(actual)

    if closing_line is None:
        line_beat = None
    else:
        closing_implied = float(closing_line.get("f1_implied_prob", 0.5))
        edge = we_said_f1 - closing_implied
        if abs(edge) <= EDGE_THRESHOLD:
            bet_signal = "pass"
            profitable = None
        elif edge > 0:
            bet_signal = "back_f1"
            profitable = (actual.get("winner") == fighter1)
        else:
            bet_signal = "back_f2"
            profitable = (actual.get("winner") == fighter2)

        line_beat = {
            "we_said_f1_prob": round(we_said_f1, 4),
            "closing_implied_prob": round(closing_implied, 4),
            "edge_pct": round(edge * 100, 2),
            "bet_signal": bet_signal,
            "would_have_been_profitable": profitable,
            "f1_implied_prob_at_close": round(closing_implied, 4),  # alias for rollup
        }

    return {
        "pick_correct": pick_correct,
        "method_correct": method_correct,
        "round_correct": round_correct,
        "brier_score": round(brier, 4),
        "log_loss": round(log_loss, 4),
        "line_beat": line_beat,
    }


def score_card(per_fight_blocks: list[dict]) -> dict[str, Any]:
    """Aggregate per-fight scoring into card-level rollup.

    Each item in per_fight_blocks must have a `scoring` key (matching the
    output of score_fight)."""
    scorings = [b["scoring"] for b in per_fight_blocks]
    n = len(scorings)
    if n == 0:
        return {"fights_scored": 0}

    pick_count = sum(1 for s in scorings if s["pick_correct"])
    brier_total = sum(s["brier_score"] for s in scorings)

    bets = [s["line_beat"] for s in scorings
            if s["line_beat"] is not None and s["line_beat"]["bet_signal"] != "pass"]
    bets_taken = len(bets)
    bets_won = sum(1 for b in bets if b["would_have_been_profitable"])

    # Hypothetical $100 unit P/L
    pl = 0.0
    for b in bets:
        if b["would_have_been_profitable"]:
            # We bet on the side we said was undervalued; payoff at closing line
            implied = b["f1_implied_prob_at_close"] if b["bet_signal"] == "back_f1" \
                else 1.0 - b["f1_implied_prob_at_close"]
            pl += _moneyline_payout(implied)
        else:
            pl -= 100.0

    roi_pct = (pl / (bets_taken * 100.0) * 100) if bets_taken > 0 else 0.0

    return {
        "fights_scored": n,
        "pick_accuracy": pick_count / n,
        "avg_brier": brier_total / n,
        "betting_record": {
            "bets_taken": bets_taken,
            "bets_won": bets_won,
            "roi_pct": round(roi_pct, 2),
            "unit_pl": round(pl, 2),
        },
    }
