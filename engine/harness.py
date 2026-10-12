"""Checks every template in a module over many seeds.

    python3 harness.py templates_t12 [--seeds 3000] [--samples 3] [--only ID]

Fails (exit 1) on any validation error, crash, or fallback problem. Also prints how many
distinct problems each template produced, warnings, and a few rendered samples to read.
"""
import argparse
import importlib
import sys
import textwrap
import traceback

import engine


def show(prob):
    out = [f"  [{prob['templateId']}] tier {prob['tier']} · {prob['topic']} · {engine.word_count(prob)} words"]
    out += textwrap.wrap(prob['stem'], 100, initial_indent='    ', subsequent_indent='    ')
    if prob.get('table'):
        t = prob['table']
        out.append('    | ' + ' | '.join(map(str, t['headers'])) + ' |')
        for row in t['rows']:
            out.append('    | ' + ' | '.join(map(str, row)) + ' |')
    out += textwrap.wrap('ASK: ' + prob['ask'], 100, initial_indent='    ', subsequent_indent='    ')
    out.append(f"    ANSWER: {prob['display']}   (tol {prob['answer']['tol']})")
    for i, s in enumerate(prob['steps'], 1):
        out += textwrap.wrap(f"{i}. {s}", 100, initial_indent='      ', subsequent_indent='         ')
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('modules', nargs='+')
    ap.add_argument('--seeds', type=int, default=3000)
    ap.add_argument('--samples', type=int, default=0)
    ap.add_argument('--only')
    a = ap.parse_args()
    before = set(engine.REGISTRY)
    for m in a.modules:
        importlib.import_module(m)
    ids = [i for i in engine.REGISTRY if i not in before]
    if a.only:
        ids = [i for i in ids if a.only in i]
    total_fail = 0
    for tid in ids:
        cls = engine.REGISTRY[tid]
        fails, distinct, giveaway, crashes = [], set(), 0, 0
        try:
            fb = engine.build(cls, 'fallback', force_fallback=True)
            errs = engine.validate(fb)
            if errs:
                fails.append(('fallback', errs))
        except Exception:
            fails.append(('fallback', [traceback.format_exc(limit=3)]))
        for i in range(a.seeds):
            try:
                p = engine.build(cls, f"h:{tid}:{i}")
            except Exception:
                crashes += 1
                if crashes <= 2:
                    fails.append((i, [traceback.format_exc(limit=4)]))
                continue
            errs = engine.validate(p)
            if errs and len(fails) < 6:
                fails.append((i, errs))
            elif errs:
                fails.append((i, None))
            distinct.add(p['stem'] + p['ask'])
            if p['core'] in p['stem'] and p['answer']['kind'] != 'money':
                giveaway += 1
        n_fail = len(fails)
        total_fail += n_fail
        status = 'OK  ' if not n_fail else 'FAIL'
        warn = f"  ⚠ answer appears in stem in {giveaway} seeds" if giveaway > a.seeds * 0.2 else ''
        print(f"{status} {tid:40s} tier {cls.tier} {cls.topic:11s} distinct {len(distinct):5d}/{a.seeds}{warn}")
        for seed, errs in fails[:6]:
            if errs:
                print(f"     seed {seed}: " + '\n       '.join(errs))
        if a.samples:
            for i in range(a.samples):
                print(show(engine.build(cls, f"sample:{tid}:{i}")))
            print()
    print(f"\n{len(ids)} templates, {total_fail} failing cases")
    sys.exit(1 if total_fail else 0)


if __name__ == '__main__':
    main()
