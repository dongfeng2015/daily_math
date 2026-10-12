# Writing templates for Molver

A daily set of short, ACT/SAT-style word problems. Players read a real situation, pull out the math
that matters, and type an exact number. No calculator, no multiple choice, nothing past algebra 2.
Answers in the app are hidden until the next day, so people argue about them; a problem must have
exactly one defensible answer.

## The contract
Read `engine.py` (top docstring + helpers) and `templates_ref.py` (two finished examples) first.
Each template is a class with `params(r)`, `solve(p)`, `render(p)` and a `fallback` dict, registered
with `@template(id=..., tier=..., topic=..., kind=..., unit=..., seconds=...)`.

- `id`: `t{tier}.{short-name}.v1` (bonus: `b.{short-name}.v1`). Unique. Never reuse.
- `topic`: one of money, percent, rates, ratio, time, averages, geometry, probability, counting,
  growth, algebra, data, units, puzzle.
- `kind`: money (solve returns int cents), int, dec (Fraction, terminating, ≤3 decimals unless the ask
  says how to round), frac (Fraction; use for probabilities and leftover-fraction answers), pct (the
  percent number as a Fraction, e.g. Fraction(25) for 25%).
- `unit`: shown after the input box and in the answer ("minutes", "gallons", "cups"). None for money
  and pct. `render` may return `unit` to override it per draw (e.g. miles vs kilometers).
- `seconds`: expected median solve time. Tier 1 ≈ 30–45, tier 2 ≈ 45–70, tier 3 ≈ 60–90,
  tier 4 ≈ 75–110, tier 5 ≈ 90–150, bonus ≈ 60–150.
- `params(r)`: draw everything with `r` (r.int, r.pick, r.sample, r.chance, r.person(), r.people(k)).
  Build valid numbers by construction where you can (pick the answer first, derive the givens).
  `raise Retry` for a bad draw. Never loop forever yourself.
- `solve(p)`: compute the answer *independently* of render, ideally a different way (brute force,
  Fraction arithmetic, formula vs. step-by-step). This is the answer key.
- `render(p)`: returns `dict(stem=..., ask=..., steps=[...], table=None|dict(headers=[...], rows=[[...]]))`.
  `steps` re-derive the numbers themselves; the LAST step must contain the answer formatted with
  `usd()` / `num()` / `frac()` / `pct()` exactly as the engine does (the harness checks this).
- `fallback`: a hand-checked params dict, used if `params` fails 200 times. Use `person('Rosa')`.

## Style guide for every problem
1. A real person or situation in the first sentence. Use `r.person()` for names and `.he/.him/.his`
   (`.He/.His` capitalized) for pronouns. Vary contexts: give most templates 2–4 context skins
   (different stories with the same math), so the same template feels new each time it returns.
2. The numbers you need are spread across 2–4 sentences, not crammed in one line.
3. Tiers 2–5: include one irrelevant detail, a number or fact that sounds useful and isn't
   (a start time, the number of people in a class, a store's opening hour). Make it natural.
4. Roughly 1 in 5 templates uses a small table (2–5 rows) for schedules, price lists, survey results.
5. The ask comes last as one plain question sentence ending in "?", and names the unit or the rounding
   ("in minutes", "to the nearest cent", "in whole gallons"). Answers are exact unless the ask says
   how to round. No negative answers.
6. No trick wording. Hard means more to think through, never a gotcha. No ambiguity: if "how much
   more" could be read two ways, rewrite it. State assumptions plainly ("at a steady rate", "the price
   doesn't change").
7. Calculator-free: stem numbers have ≤ 5 significant digits; no step needs more than 2-digit × 2-digit
   multiplication or long division by a 1-digit number. Choose friendly numbers.
8. Steps: 2–5 short lines a person can follow in 20 seconds. Show the shortcut a strong student would
   use (10% then half for 15%; ×0.8 for 20% off).
9. Word count of stem + ask: tier 1: 20–75, tiers 2–5: 35–125, bonus 20–125. Aim for 40–90 on tiers 2–5.
10. Grammar: use `plural(n, 'cup')`, `a_an(n)` ("an 85"), `word(n)` for small numbers at sentence
    start (with `cap`). Don't end a sentence on "a.m." or "p.m." (you'd get "a.m.."). Avoid "1 people".
11. Plain American English, everyday settings (groceries, commuting, sports, cooking, home projects,
    school, jobs, travel, savings). No brand names, no real public figures, nothing grim.

Tier meaning: 1 Warm-up (one or two easy steps) · 2 Everyday (two steps, real decision or conversion)
· 3 Two-step (set up and combine) · 4 Tricky (needs an idea: rates add, area scales by square, etc.)
· 5 Stretch (probability, counting, algebra setups, hardest of the day) · 6 Bonus (a classic puzzle
with a real-world skin; satisfying "aha", typed numeric answer).

## Checking
    python3 harness.py <your_module> --seeds 10000          # must end with "0 failing cases"
    python3 harness.py <your_module> --seeds 200 --samples 4 # read the samples like a picky editor

Read samples for every template: is the answer unambiguous? Do the numbers look natural? Is the
worked solution right and easy to follow? Does the irrelevant detail read naturally? Fix and rerun.
