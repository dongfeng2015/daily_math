"""Builds the year of daily puzzles.

    python3 build_dataset.py [--start 2026-10-05] [--end 2027-10-31] [--out ../data]

Rules for each day
  * Weekdays and Sundays: five problems, one per tier 1-5.
  * Saturdays ("the Saturday Seven"): seven problems, tiers 1,2,3,3,4,4,5.
  * Bonus: on about 30% of non-Saturday days, chosen at random, one extra puzzle problem.
  * No two problems in a day share a topic or a template, and no person's name repeats in a day.
  * A template doesn't come back until most of its tier has been used (least-recently-used pick with
    a minimum gap), so the same problem shape returns about every 1.5-2 weeks with new numbers and story.
Also writes a practice pool (unscored sets, separate templates draws) and a review CSV.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import random
from collections import Counter, defaultdict

import engine
import templates_ref, templates_t12, templates_t34, templates_t5b  # noqa: F401  (register templates)

LAUNCH = '2026-10-05'
WEEKDAY_TIERS = [1, 2, 3, 4, 5]
SATURDAY_TIERS = [1, 2, 3, 3, 4, 4, 5]
BONUS_RATE = 0.30
PRACTICE_SETS = 60


def seed_int(s):
    return int(hashlib.sha256(s.encode()).hexdigest()[:12], 16)


def public(prob):
    p = dict(prob)
    p.pop('core', None)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default=LAUNCH)
    ap.add_argument('--end', default='2027-10-31')
    ap.add_argument('--out', default='../data')
    a = ap.parse_args()

    pools = defaultdict(list)
    for tid, cls in engine.REGISTRY.items():
        pools[cls.tier].append(cls)
    for t in pools:
        pools[t].sort(key=lambda c: c.id)
    print({t: len(v) for t, v in sorted(pools.items())})

    last_used = {}          # template id -> day index
    usage = Counter()
    gaps = defaultdict(list)
    days = []
    start = dt.date.fromisoformat(a.start)
    end = dt.date.fromisoformat(a.end)
    launch = dt.date.fromisoformat(LAUNCH)
    errors = []

    def choose(tier, di, rng, taken_ids, taken_topics, min_gap):
        cands = [c for c in pools[tier] if c.id not in taken_ids and c.topic not in taken_topics
                 and di - last_used.get(c.id, -999) >= min_gap]
        if not cands:
            return None
        # least recently used first; random tiebreak
        rng.shuffle(cands)
        cands.sort(key=lambda c: last_used.get(c.id, -999))
        return cands[0] if rng.random() < 0.7 else cands[min(1, len(cands) - 1)]

    d, di = start, 0
    while d <= end:
        date = d.isoformat()
        rng = random.Random(seed_int('schedule:' + date))
        sat = d.weekday() == 5
        tiers = SATURDAY_TIERS if sat else WEEKDAY_TIERS
        used_names = set()
        probs, ids, topics = [], set(), set()
        for slot, tier in enumerate(tiers):
            pool_n = len(pools[tier])
            cls = None
            for min_gap in (pool_n - 2, pool_n // 2, 3, 0):
                cls = choose(tier, di, rng, ids, topics, min_gap)
                if cls:
                    break
            assert cls, (date, tier)
            if cls.id in last_used:
                gaps[cls.id].append(di - last_used[cls.id])
            last_used[cls.id] = di
            usage[cls.id] += 1
            ids.add(cls.id)
            topics.add(cls.topic)
            prob = engine.build(cls, f"{date}:{slot}:{cls.id}", used_names)
            errs = engine.validate(prob)
            if errs:
                errors.append((date, cls.id, errs))
            probs.append(prob)
        bonus = None
        if not sat and rng.random() < BONUS_RATE:
            cls = choose(6, di, rng, ids, set(), len(pools[6]) - 3) or choose(6, di, rng, ids, set(), 0)
            last_used[cls.id] = di
            usage[cls.id] += 1
            bonus = engine.build(cls, f"{date}:bonus:{cls.id}", used_names)
            errs = engine.validate(bonus)
            if errs:
                errors.append((date, cls.id, errs))
        days.append({
            'date': date, 'no': (d - launch).days + 1, 'weekday': d.strftime('%A'),
            'kind': 'saturday' if sat else 'daily',
            'seconds': sum(p['seconds'] for p in probs),
            'problems': probs, 'bonus': bonus,
        })
        d += dt.timedelta(days=1)
        di += 1

    # practice pool: weekday-shaped sets from separate seeds
    practice = []
    for i in range(PRACTICE_SETS):
        rng = random.Random(seed_int(f'practice:{i}'))
        used_names, probs, topics = set(), [], set()
        for slot, tier in enumerate(WEEKDAY_TIERS):
            cands = [c for c in pools[tier] if c.topic not in topics]
            cls = rng.choice(cands)
            topics.add(cls.topic)
            prob = engine.build(cls, f"practice:{i}:{slot}:{cls.id}", used_names)
            if engine.validate(prob):
                errors.append((f'practice {i}', cls.id, engine.validate(prob)))
            probs.append(prob)
        practice.append({'id': i + 1, 'problems': probs})

    if errors:
        for e in errors[:20]:
            print('ERROR', e)
        raise SystemExit(f"{len(errors)} invalid problems")

    out = {
        'title': 'Molver', 'version': 2,
        'generated': dt.date.today().isoformat(), 'launch': LAUNCH,
        'range': [a.start, a.end],
        'rules': {'weekday_tiers': WEEKDAY_TIERS, 'saturday_tiers': SATURDAY_TIERS, 'bonus_rate': BONUS_RATE},
        'templates': {tid: {'tier': c.tier, 'topic': c.topic} for tid, c in sorted(engine.REGISTRY.items())},
        'days': [{**dday, 'problems': [public(p) for p in dday['problems']],
                  'bonus': public(dday['bonus']) if dday['bonus'] else None} for dday in days],
        'practice': [{**s, 'problems': [public(p) for p in s['problems']]} for s in practice],
    }
    import os
    os.makedirs(a.out, exist_ok=True)
    with open(f"{a.out}/puzzles.json", 'w') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))

    with open(f"{a.out}/puzzles-review.csv", 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['date', 'no', 'weekday', 'slot', 'tier', 'topic', 'template', 'question', 'table', 'answer',
                    'accepts within', 'explanation'])
        for dday in days:
            rows = [(str(i + 1), p) for i, p in enumerate(dday['problems'])]
            if dday['bonus']:
                rows.append(('bonus', dday['bonus']))
            for slot, p in rows:
                table = ''
                if p.get('table'):
                    t = p['table']
                    table = ' | '.join(map(str, t['headers'])) + ' / ' + ' / '.join(' | '.join(map(str, r)) for r in t['rows'])
                w.writerow([dday['date'], dday['no'], dday['weekday'], slot, p['tierName'], p['topic'], p['templateId'],
                            p['stem'] + ' ' + p['ask'], table, p['display'], p['answer']['tol'],
                            ' '.join(f"{i}. {s}" for i, s in enumerate(p['steps'], 1))])

    n_probs = sum(len(x['problems']) for x in days)
    n_bonus = sum(1 for x in days if x['bonus'])
    secs = [x['seconds'] for x in days if x['kind'] == 'daily']
    ssecs = [x['seconds'] for x in days if x['kind'] == 'saturday']
    print(f"{len(days)} days ({a.start} → {a.end}), {n_probs} problems + {n_bonus} bonus, {len(practice)} practice sets")
    print(f"target time: weekday {min(secs)}-{max(secs)}s (avg {sum(secs)//len(secs)}), "
          f"Saturday {min(ssecs)}-{max(ssecs)}s (avg {sum(ssecs)//len(ssecs)})")
    mins = {t: min(g) for t, g in gaps.items()}
    by_tier = defaultdict(list)
    for t, m in mins.items():
        by_tier[engine.REGISTRY[t].tier].append(m)
    print('shortest repeat gap by tier (days):', {t: min(v) for t, v in sorted(by_tier.items())})
    print('uses per template by tier:', {t: (min(usage[c.id] for c in pools[t]), max(usage[c.id] for c in pools[t]))
                                         for t in sorted(pools)})
    print(f"size: {os.path.getsize(f'{a.out}/puzzles.json') / 1e6:.2f} MB")


if __name__ == '__main__':
    main()
