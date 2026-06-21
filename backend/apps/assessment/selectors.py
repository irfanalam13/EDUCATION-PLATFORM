import math
import random
from typing import Dict, List

from django.db.models import QuerySet

from apps.assessment.models import MCQQuestion
from apps.assessment.models.bank import Difficulty


def _normalize_mix(mix: Dict) -> Dict[str, float]:
    # Default if empty: evenly distribute
    if not mix:
        return {"EASY": 0.33, "MEDIUM": 0.34, "HARD": 0.33}

    total = sum(float(v) for v in mix.values()) if mix else 0.0
    if total <= 0:
        return {"EASY": 0.33, "MEDIUM": 0.34, "HARD": 0.33}

    return {k: float(v) / total for k, v in mix.items()}


def _counts_from_mix(total_count: int, mix: Dict[str, float]) -> Dict[str, int]:
    # Convert ratios -> integer counts, fix rounding drift
    keys = ["EASY", "MEDIUM", "HARD"]
    raw = {k: total_count * mix.get(k, 0.0) for k in keys}
    counts = {k: int(math.floor(raw[k])) for k in keys}
    drift = total_count - sum(counts.values())

    # Distribute drift by largest fractional parts
    frac = sorted(keys, key=lambda k: (raw[k] - math.floor(raw[k])), reverse=True)
    for i in range(drift):
        counts[frac[i % len(frac)]] += 1
    return counts


def mcq_bank_queryset(scope: Dict) -> QuerySet[MCQQuestion]:
    qs = MCQQuestion.objects.filter(is_active=True)

    subject = scope.get("subject") if scope else None
    chapter = scope.get("chapter") if scope else None
    topic = scope.get("topic") if scope else None

    # Scope values are academics PKs now (FK columns).
    if subject:
        qs = qs.filter(subject_id=subject)
    if chapter:
        qs = qs.filter(chapter_id=chapter)
    if topic:
        qs = qs.filter(topic_id=topic)
    return qs


def select_mcq_questions_for_session(scope: Dict, count: int, difficulty_mix: Dict) -> List[MCQQuestion]:
    mix = _normalize_mix(difficulty_mix)
    counts = _counts_from_mix(count, mix)

    qs = mcq_bank_queryset(scope)

    picked: List[MCQQuestion] = []
    for diff_key, need in counts.items():
        if need <= 0:
            continue
        diff_val = getattr(Difficulty, diff_key)
        candidates = list(qs.filter(difficulty=diff_val).order_by("?")[:need])
        picked.extend(candidates)

    # If not enough questions in some difficulty, fill from remaining pool
    if len(picked) < count:
        remaining_needed = count - len(picked)
        used_ids = [q.id for q in picked]
        filler = list(qs.exclude(id__in=used_ids).order_by("?")[:remaining_needed])
        picked.extend(filler)

    # If still short, just return what we have
    random.shuffle(picked)
    return picked[:count]
