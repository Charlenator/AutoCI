"""Seed generator — produces realistic synthetic recruitment data for AutoCI demos.

Each role has a deliberate KPI fingerprint so a Kaizen has something meaningful to find:
  - Senior Java Developer  → bad TTF, mediocre OAR (primary demo target)
  - Product Manager        → healthy, hit targets (control case)
  - UX Designer            → poor stage conversion (Screening dropoff)
  - Data Engineer          → good TTF but skewed source mix (low-yield channels)
  - DevOps Engineer        → all green (proves the pipeline works)

Run: python supabase/seed_generator.py > supabase/seed_v2_pipeline.sql
Then load via Supabase MCP or SQL editor. Re-running with the same seed produces identical UUIDs."""

import random
import uuid
from datetime import date, timedelta

NAMESPACE = uuid.UUID("00000000-0000-0000-0000-000000000001")
random.seed(42)

# Reuse existing role and interviewer UUIDs from seed.sql
ROLES = {
    "Senior Java Developer": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "Product Manager":       "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "UX Designer":           "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "Data Engineer":         "d4e5f6a7-b8c9-0123-defa-234567890123",
    "DevOps Engineer":       "e5f6a7b8-c9d0-1234-efab-345678901234",
}
INTERVIEWERS = [
    "f6a7b8c9-d0e1-2345-fabc-456789012345",
    "a7b8c9d0-e1f2-3456-abcd-567890123456",
    "b8c9d0e1-f2a3-4567-bcde-678901234567",
    "c9d0e1f2-a3b4-5678-cdef-789012345678",
    "d0e1f2a3-b4c5-6789-defa-890123456789",
]

# Per-role recipe — drives conversion / OAR / TTF independently
RECIPES = {
    "Senior Java Developer": {
        "n_candidates": 35, "screening_pass": 0.55, "interview1_pass": 0.50,
        "interview2_pass": 0.55, "offer_extend_rate": 0.85, "offer_accept_rate": 0.55,  # bad OAR
        "ttf_mean": 58, "ttf_stdev": 12,
        "source_mix": [("LinkedIn", 0.45), ("Referral", 0.20), ("Direct", 0.10), ("Indeed", 0.15), ("Agency", 0.10)],
    },
    "Product Manager": {
        "n_candidates": 30, "screening_pass": 0.70, "interview1_pass": 0.65,
        "interview2_pass": 0.70, "offer_extend_rate": 0.90, "offer_accept_rate": 0.85,
        "ttf_mean": 38, "ttf_stdev": 8,
        "source_mix": [("LinkedIn", 0.35), ("Referral", 0.30), ("Direct", 0.15), ("Indeed", 0.10), ("Agency", 0.10)],
    },
    "UX Designer": {
        "n_candidates": 28, "screening_pass": 0.40, "interview1_pass": 0.65,
        "interview2_pass": 0.70, "offer_extend_rate": 0.85, "offer_accept_rate": 0.86,
        "ttf_mean": 32, "ttf_stdev": 7,
        "source_mix": [("LinkedIn", 0.40), ("Referral", 0.15), ("Direct", 0.20), ("Indeed", 0.15), ("Agency", 0.10)],
    },
    "Data Engineer": {
        "n_candidates": 30, "screening_pass": 0.65, "interview1_pass": 0.60,
        "interview2_pass": 0.65, "offer_extend_rate": 0.88, "offer_accept_rate": 0.78,
        "ttf_mean": 36, "ttf_stdev": 8,
        "source_mix": [("Indeed", 0.45), ("Agency", 0.30), ("LinkedIn", 0.15), ("Direct", 0.05), ("Referral", 0.05)],
    },
    "DevOps Engineer": {
        "n_candidates": 25, "screening_pass": 0.70, "interview1_pass": 0.65,
        "interview2_pass": 0.75, "offer_extend_rate": 0.92, "offer_accept_rate": 0.88,
        "ttf_mean": 26, "ttf_stdev": 6,
        "source_mix": [("Referral", 0.40), ("LinkedIn", 0.30), ("Direct", 0.15), ("Indeed", 0.10), ("Agency", 0.05)],
    },
}

START_DATE = date(2025, 8, 1)
END_DATE = date(2026, 4, 15)
DATE_SPAN_DAYS = (END_DATE - START_DATE).days

DECLINE_REASONS = [
    "Higher compensation offer elsewhere",
    "Counter offer from current employer",
    "Lost to competitor",
    "Role scope mismatch",
    "Family / relocation reasons",
]


def pick_source(mix: list[tuple[str, float]]) -> str:
    r = random.random()
    cum = 0.0
    for name, p in mix:
        cum += p
        if r <= cum:
            return name
    return mix[-1][0]


def cand_uuid(role: str, idx: int) -> str:
    return str(uuid.uuid5(NAMESPACE, f"v2-cand-{role}-{idx}"))


def offer_uuid(role: str, idx: int) -> str:
    return str(uuid.uuid5(NAMESPACE, f"v2-offer-{role}-{idx}"))


def hire_uuid(role: str, idx: int) -> str:
    return str(uuid.uuid5(NAMESPACE, f"v2-hire-{role}-{idx}"))


def gen_pipeline(role: str, recipe: dict) -> tuple[list, list, list, list]:
    """Return (candidates, events, hires, offer_outcomes) rows for one role."""
    candidates, events, hires, offers = [], [], [], []
    role_id = ROLES[role]
    ttf_target = recipe["ttf_mean"]

    for i in range(recipe["n_candidates"]):
        cand_id = cand_uuid(role, i)
        applied = START_DATE + timedelta(days=random.randint(0, DATE_SPAN_DAYS - 90))
        source = pick_source(recipe["source_mix"])
        ext_id = f"V2-{role[:3].upper()}-{i:03d}"
        candidates.append((cand_id, role_id, source, applied.isoformat(), ext_id))

        # Stage progression — each stage either advances or rejects
        cursor = applied
        events.append((cand_id, "Applied", cursor.isoformat(), "Advanced", None, "Application received"))

        # Screening
        cursor += timedelta(days=random.randint(3, 14))
        if random.random() > recipe["screening_pass"]:
            events.append((cand_id, "Screening", cursor.isoformat(), "Rejected",
                           random.choice(INTERVIEWERS), "Did not pass screening"))
            continue
        events.append((cand_id, "Screening", cursor.isoformat(), "Advanced",
                       random.choice(INTERVIEWERS), "Screening completed"))

        # Interview 1
        cursor += timedelta(days=random.randint(5, 14))
        if random.random() > recipe["interview1_pass"]:
            events.append((cand_id, "Interview 1", cursor.isoformat(), "Rejected",
                           random.choice(INTERVIEWERS), "Failed technical / role fit"))
            continue
        events.append((cand_id, "Interview 1", cursor.isoformat(), "Advanced",
                       random.choice(INTERVIEWERS), "Technical interview passed"))

        # Interview 2
        cursor += timedelta(days=random.randint(5, 14))
        if random.random() > recipe["interview2_pass"]:
            events.append((cand_id, "Interview 2", cursor.isoformat(), "Rejected",
                           random.choice(INTERVIEWERS), "Cultural / system design"))
            continue
        events.append((cand_id, "Interview 2", cursor.isoformat(), "Advanced",
                       random.choice(INTERVIEWERS), "Cleared final round"))

        # Offer extended?
        if random.random() > recipe["offer_extend_rate"]:
            continue  # held back, no offer

        cursor += timedelta(days=random.randint(3, 8))
        events.append((cand_id, "Offer", cursor.isoformat(), "Offer Extended",
                       random.choice(INTERVIEWERS), "Offer sent"))

        # Accept or decline?
        accepted = random.random() <= recipe["offer_accept_rate"]
        outcome = "Accepted" if accepted else "Declined"
        decline = None if accepted else random.choice(DECLINE_REASONS)
        offers.append((offer_uuid(role, i), cand_id, role_id, outcome, decline))

        if accepted:
            # Hire — TTF noisy around target
            ttf_actual = max(15, int(random.gauss(recipe["ttf_mean"], recipe["ttf_stdev"])))
            offer_date = applied + timedelta(days=ttf_actual - 5)
            start = offer_date + timedelta(days=21)
            salary = random.randint(70, 130) * 10000
            hires.append((hire_uuid(role, i), cand_id, role_id,
                          offer_date.isoformat(), start.isoformat(), salary, True))
        else:
            offer_date = applied + timedelta(days=random.randint(28, 50))
            salary = random.randint(70, 130) * 10000
            hires.append((hire_uuid(role, i), cand_id, role_id,
                          offer_date.isoformat(), None, salary, False))

    return candidates, events, hires, offers


def sql_str(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def values_clause(rows: list[tuple]) -> str:
    return ",\n  ".join("(" + ", ".join(sql_str(c) for c in row) + ")" for row in rows)


def main() -> None:
    all_cands, all_events, all_hires, all_offers = [], [], [], []
    for role, recipe in RECIPES.items():
        c, e, h, o = gen_pipeline(role, recipe)
        all_cands += c
        all_events += e
        all_hires += h
        all_offers += o

    print("-- AutoCI Seed v2 — multi-role pipeline (~200 events)")
    print("-- Generated by seed_generator.py (deterministic, seed=42).")
    print("-- WIPES candidates / pipeline_events / hires / offer_outcomes — keeps roles, interviewers, benchmarks.")
    print()
    print("BEGIN;")
    print("DELETE FROM offer_outcomes;")
    print("DELETE FROM hires;")
    print("DELETE FROM pipeline_events;")
    print("DELETE FROM candidates;")
    print()
    print("INSERT INTO candidates (candidate_id, role_id, source_channel, applied_date, external_id) VALUES")
    print("  " + values_clause(all_cands) + ";")
    print()
    print("INSERT INTO pipeline_events (candidate_id, stage, event_date, outcome, interviewer_id, notes) VALUES")
    print("  " + values_clause(all_events) + ";")
    print()
    print("INSERT INTO hires (hire_id, candidate_id, role_id, offer_date, start_date, salary, accepted) VALUES")
    print("  " + values_clause(all_hires) + ";")
    print()
    print("INSERT INTO offer_outcomes (offer_id, candidate_id, role_id, outcome, decline_reason) VALUES")
    print("  " + values_clause(all_offers) + ";")
    print()
    print("COMMIT;")
    print()
    print(f"-- Totals: {len(all_cands)} candidates, {len(all_events)} pipeline events, "
          f"{len(all_hires)} hires, {len(all_offers)} offer outcomes")


if __name__ == "__main__":
    main()
