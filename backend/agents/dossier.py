"""Adapter: scrape_ufc_fighter.py output → dossier shape per
UFC agents/_shared/data-contract.md.

Field-name and type mismatches handled here so the agents see exactly the
contract they document. Missing fields stay missing — agents lower confidence
themselves rather than receiving fabricated values."""

import datetime
import re


_DOB_FORMATS = ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d", "%m/%d/%Y")
_FIGHT_DATE_FORMATS = ("%b %d, %Y", "%B %d, %Y")


def _parse_dob_iso(dob_str: str) -> str | None:
    if not dob_str or dob_str in ("N/A", "--"):
        return None
    for fmt in _DOB_FORMATS:
        try:
            return datetime.datetime.strptime(dob_str.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _parse_fight_date_iso(date_str: str) -> str | None:
    if not date_str or date_str == "N/A":
        return None
    cleaned = date_str.replace(".", "")
    for fmt in _FIGHT_DATE_FORMATS:
        try:
            return datetime.datetime.strptime(cleaned.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _height_to_inches(height_str: str) -> int | None:
    """6'4\" → 76. Tolerates 6' 4\", 6'4, 6 ft 4 in."""
    if not height_str or height_str in ("N/A", "--"):
        return None
    m = re.search(r"(\d+)\s*[′'][\s]*(\d+)", height_str)
    if not m:
        return None
    return int(m.group(1)) * 12 + int(m.group(2))


def _reach_to_inches(reach_str: str) -> int | None:
    if not reach_str or reach_str in ("N/A", "--"):
        return None
    m = re.search(r"(\d+(?:\.\d+)?)", reach_str)
    return int(float(m.group(1))) if m else None


def _percent_to_decimal(pct_str: str) -> float | None:
    """'50%' → 0.50, '0.50' → 0.50, returns None if unparseable or N/A."""
    if pct_str is None or pct_str in ("N/A", "--", ""):
        return None
    if isinstance(pct_str, (int, float)):
        v = float(pct_str)
        return v / 100 if v > 1 else v
    m = re.search(r"(\d+(?:\.\d+)?)", str(pct_str))
    if not m:
        return None
    v = float(m.group(1))
    return v / 100 if v > 1 else v


def _to_float(s) -> float | None:
    if s is None or s in ("N/A", "--", ""):
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _last_fight_date(fight_history: list[dict]) -> str | None:
    for f in fight_history or []:
        iso = _parse_fight_date_iso(f.get("date", ""))
        if iso:
            return iso
    return None


def _last_5_fights(fight_history: list[dict]) -> list[dict]:
    out = []
    for f in (fight_history or [])[:5]:
        out.append({
            "date": _parse_fight_date_iso(f.get("date", "")) or f.get("date", ""),
            "opponent": f.get("opponent", ""),
            "result": f.get("result", ""),
            "method": f.get("method", ""),
            "round": f.get("round", ""),
            "time": f.get("time", ""),
        })
    return out


def build_dossier(scrape_data: dict) -> dict:
    """Convert scrape_ufc_fighter (or scrape_debut_fighter) output to the dossier
    shape agents expect. Missing fields are left out so the agent's data_caveats
    logic surfaces them honestly."""
    striking = scrape_data.get("striking", {}) or {}
    grappling = scrape_data.get("grappling", {}) or {}
    intangibles = scrape_data.get("intangibles", {}) or {}
    fight_history = scrape_data.get("fight_history", []) or []
    win_methods = scrape_data.get("win_methods", {}) or {}

    record = scrape_data.get("record", {}) or {}

    def _int(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return 0

    record_wins = _int(record.get("wins"))
    record_losses = _int(record.get("losses"))
    record_draws = _int(record.get("draws"))
    ko_wins_raw = _int(win_methods.get("ko"))
    sub_wins_raw = _int(win_methods.get("sub"))
    total_wins = record_wins

    # Dossier-shape striking_stats
    striking_stats = {}
    slpm = _to_float(striking.get("slpm"))
    if slpm is not None:
        striking_stats["SLpM"] = slpm
    sapm = _to_float(striking.get("sapm"))
    if sapm is not None:
        striking_stats["SApM"] = sapm
    str_acc = _percent_to_decimal(striking.get("str_acc"))
    if str_acc is not None:
        striking_stats["str_acc"] = str_acc
    str_def = _percent_to_decimal(striking.get("str_def"))
    if str_def is not None:
        striking_stats["str_def"] = str_def
    # knockdown_avg not in scrape data — derive proxy from KO rate if record present
    if total_wins > 0:
        striking_stats["ko_finish_rate"] = round(ko_wins_raw / total_wins, 3)

    grappling_stats = {}
    td_avg = _to_float(grappling.get("td_avg"))
    if td_avg is not None:
        grappling_stats["td_avg"] = td_avg
    td_acc = _percent_to_decimal(grappling.get("td_acc"))
    if td_acc is not None:
        grappling_stats["td_acc"] = td_acc
    td_def = _percent_to_decimal(grappling.get("td_def"))
    if td_def is not None:
        grappling_stats["td_def"] = td_def
    sub_avg = _to_float(grappling.get("sub_avg"))
    if sub_avg is not None:
        grappling_stats["sub_avg"] = sub_avg
    if total_wins > 0:
        grappling_stats["sub_finish_rate"] = round(sub_wins_raw / total_wins, 3)

    dossier = {
        "name": scrape_data["name"],
        "record": {
            "wins": record_wins,
            "losses": record_losses,
            "draws": record_draws,
        },
    }

    dob_iso = _parse_dob_iso(scrape_data.get("dob", ""))
    if dob_iso:
        dossier["dob"] = dob_iso

    height_in = _height_to_inches(scrape_data.get("height", ""))
    if height_in:
        dossier["height_in"] = height_in
    reach_in = _reach_to_inches(scrape_data.get("reach", ""))
    if reach_in:
        dossier["reach_in"] = reach_in
    if scrape_data.get("stance"):
        dossier["stance"] = scrape_data["stance"]
    if scrape_data.get("weight"):
        dossier["weight_class"] = scrape_data["weight"]

    if striking_stats:
        dossier["striking_stats"] = striking_stats
    if grappling_stats:
        dossier["grappling_stats"] = grappling_stats

    last_5 = _last_5_fights(fight_history)
    if last_5:
        dossier["last_5_fights"] = last_5

    last_fd = _last_fight_date(fight_history)
    if last_fd:
        dossier["last_fight_date"] = last_fd

    if intangibles.get("camp"):
        dossier["camp"] = intangibles["camp"]
    if intangibles.get("head_coach"):
        dossier["head_coach"] = intangibles["head_coach"]

    if scrape_data.get("ufc_debut"):
        dossier["ufc_debut"] = True
        dossier["debut_source"] = scrape_data.get("debut_source", "Tapology")

    return dossier
