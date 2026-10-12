# Molver — Project Plan

**Owner:** Dong · **Plan created:** 2026-10-07 · **Last updated:** 2026-10-12 · **Source of truth (from 2026-10-12):** the `daily_math` folder on Dong's Mac (`~/daily_math`). Copies in the Claude Project may lag behind it.

---

## 1. What we're building

The NYT Mini, but for math. Once a day, everyone gets the same short set of word problems. You read, you think, you type an answer. A timer runs, a streak builds, and at the end you text your friends a little emoji grid. A good day takes under five minutes; a great day feels like you earned it. On Saturdays the set is bigger (the Saturday Seven), and some days hide a bonus puzzle.

The skill being trained is the one the ACT and SAT actually test: reading a few sentences of real-world situation, pulling out the math that matters, ignoring what doesn't, and getting to an exact number without a calculator. Later, the same engine powers head-to-head battles in the spirit of school math competitions.

### Design principles (and why)

- **Short.** Weekday sets are 5 problems (about a minute each, ACT pace). Saturdays are 7, like the NYT's bigger Saturday puzzle. Short is what makes it a daily habit instead of homework.
- **Reading is the point.** Stems run 40–110 words (shorter for the warm-up), are set in a real situation, and usually include one detail that doesn't matter.
- **A little hard.** Difficulty ramps across the set from warm-up to stretch. Target: median score 3–4 out of 5.
- **Always correct.** Every answer is computed from the problem's own parameters by an independent solver and checked by the harness (§5, A1). One wrong answer key does more damage to trust than ten boring problems.
- **Typed answers only.** No multiple choice. No calculus, no calculator needed.
- **Same set for everyone.** That's what makes sharing meaningful and what later makes competition fair.
- **Solutions are sealed until tomorrow.** Players see right or wrong, but not the answer or the worked solution, so they talk it over with each other. The answer key and explanation ship in the dataset; the app decides when to show them (decision #10).
- **Pre-built, not generated on the day.** The whole year's problems, answers and explanations are generated ahead of time into one reviewed data file. The app looks up the player's local date.

---

## 2. Where we are (2026-10-10)

**Molver** (formerly Back of the Envelope) is live at **https://molver.net** (also https://daily-math.dongfeng2015.workers.dev):

- Loads `puzzles.json`: **2026-10-05 → 2027-10-31, 392 days, 2,072 problems, 56 Saturday Sevens, 107 bonus days, 60 practice sets.** If a date is past the end of the file, it reuses an earlier day on the same weekday so the site never goes blank.
- Weekdays and Sundays: 5 problems (Warm-up → Everyday → Two-step → Tricky → Stretch). Saturdays: 7 (tiers 1, 2, 3, 3, 4, 4, 5). Bonus: about 30% of non-Saturday days, chosen at random; it's offered after the main set, doesn't count toward the score, and adds a ⭐ to the share.
- Two tries per problem (decided 2026-10-12). Any solve, first or second try, shares as 🟩 (changed 2026-10-12: a first miss is often just a typo); a miss is 🟥. After the second miss the player sees the answer; the worked solution stays sealed until the next day. Solutions open the next day: "Yesterday's solutions" on the start screen, with a date picker back through the archive. Practice sets show answers immediately.
- Share block shows a Wordle-style result (`Molver No. 6 · Saturday Seven` / `🟩🟥🟩🟩🟩🟩🟩` / `6/7 in 7:42`) with **Text it** (opens an SMS with the result pre-filled), **Share…** (the phone's share sheet, where supported) and **Copy**.
- Timer runs only while a problem is open, and pauses when the tab is hidden. Streak, practice mode, scratch pad and dark mode carry over from v1.
- No accounts. Progress lives in the browser.

Source lives in `daily-math/` in the Project (and in the source zip):

```
app/index.html        the web app        app/puzzles.json   copy of the dataset
data/puzzles.json     the year           data/puzzles-review.csv   one row per problem, for reading/editing
engine/engine.py      template contract, formatting, answer tolerance, validation
engine/STYLE.md       writing rules      engine/templates_*.py   71 templates
engine/harness.py     checks templates   engine/build_dataset.py  builds the year
```

Known gaps:
1. **Answers are in the data file the browser downloads.** Anyone who opens dev tools can read tomorrow's set and today's answers. Fine for friends; fix with B2 (server serves one day at a time, without answers).
2. **Progress lives only in this browser** (B1).
3. **`seconds` estimates are guesses.** Weekday sets estimate 350–400 s, a bit over the 3–5 minute target; calibrate with real data (A5).
4. **Repeat spacing.** With 11–12 templates per tier, a problem shape returns every 9–12 days on average (5–6 at worst for tiers 3–4, which Saturdays use twice), always with new numbers, names and story. More templates per tier lengthens this.

---

## 3. Tracks

| Track | Lane | Runs |
|---|---|---|
| **P** | Platform floor: repo, build, tests, hosting, analytics | Next |
| **A** | Daily puzzle: problem engine, content, solo experience | Mostly done for v1 |
| **B** | Accounts & community: sync, leaderboards, archive | After public launch |
| **C** | Head-to-head battles | After B2 |

---

## 4. Track P — Platform floor

### P0 · Repo, build, tests
- Put `daily-math/` in a git repo. Keep the Python engine (it's the content pipeline; it runs at build time, not in the browser).
- CI: `python3 harness.py templates_ref templates_t12 templates_t34 templates_t5b --seeds 10000` and `python3 build_dataset.py` must pass; a Playwright smoke test plays one weekday, one Saturday and one bonus day (the script used on 2026-10-10 is the starting point).
- Optional later: port the app to Vite + TypeScript when it grows past one file.

### P1 · Hosting — ✅ live 2026-10-12
- Live at **https://daily-math.dongfeng2015.workers.dev** (Cloudflare Workers, static assets from `./app`, config in `wrangler.jsonc`).
- GitHub repo **dongfeng2015/daily_math** (private) is connected to Cloudflare; every push to `main` deploys.
- Share text ends with the site link (`CONFIG.shareUrl`). Custom domain (#4) can be attached to the same Cloudflare project later.

---

## 5. Track A — The daily puzzle

### A0 · Prototype fixes — ✅ done 2026-10-10
- Timer pauses when the tab is hidden.
- Unbounded retries replaced: `params()` gets 200 draws, then a hand-checked `fallback`.

### A1 · Template contract + harness — ✅ done 2026-10-10 (Python)
Contract in `engine/engine.py`: each template has `params(r)`, an independent `solve(p)`, `render(p)` → stem/ask/steps/table, and a `fallback`. Money is integer cents; answer kinds money/int/dec/frac/pct with per-kind tolerance (`answer.tol` in the data). The harness runs 10,000 seeds per template and fails on: last worked step not matching the solver's answer, bad text (NaN, None, doubled spaces), word count out of range, operands over 5 significant digits, decimals over 3 places without a rounding instruction, non-positive answers, or a bad fallback.

### A2 · Content library — ✅ v1 done 2026-10-10
71 templates: tier 1 ×12, tier 2 ×12, tier 3 ×12, tier 4 ×11, tier 5 ×12, bonus ×12. Most have 2–4 story skins. Written against `engine/STYLE.md` by three writers in parallel, then an independent reviewer re-solved samples of every template from the question text alone and fixed 19 templates (one real ambiguity in the survey/Venn template, heavy arithmetic in right-triangle, round-trip-speed, dilute-mix, combined-average and others, plus wording). Harness: 71 templates, 0 failing cases at 10,000 seeds.
- **Next:** grow to 100+ (about 20 per tier) so shapes return less often; owner reads `data/puzzles-review.csv` and flags anything to cut or reword.

### A3 · Daily scheduler — ✅ done 2026-10-10
`engine/build_dataset.py` precomputes every day. Rules: one template per slot by tier; no two problems in a day share a topic or template; no name repeats within a day; least-recently-used template pick with a minimum gap of (pool size − 2) days, relaxed only if nothing fits. **Amended:** the 21-day no-repeat rule isn't possible with 12 templates per tier (one per tier per day); it returns once tiers have ~25 templates. Puzzle date = player's local date; No. 1 = 2026-10-05.

### A4 · Solo experience polish — 🔶 partly done
Done: sealed solutions + yesterday's solutions archive, SMS/share-sheet/copy share, Saturday Seven, bonus, practice from a fixed pool. Still open: stats screen (played, solve rate, streaks, score bars), first-visit "how to play", full accessibility pass (axe), Playwright in CI.

### A5 · Calibration — ⬜ blocked on owner #5
Anonymous events (set started; each problem's templateId, correct, seconds; set finished). Weekly review re-tiers or rewords templates whose median time is > 1.5× `seconds` or whose solve rate is < 25% (or > 95% outside tier 1). Rebuild the dataset after changes; days already played keep their problems (rebuild only future dates).

**Launch gate:** harness green, owner has read a sample of the review CSV, hosting + domain set, A4 a11y pass, a week of tester data reviewed.

---

## 6. Track B — Accounts & community (after launch)

Skipped for now by owner decision (2026-10-10): no user creation; sharing is by text message, like early Wordle.

### B1 · Accounts & sync — *preflight required*
Spec first (`docs/specs/`): sign-in method, stored data, deletion. Local progress merges into the account on first sign-in (keep the longer streak and the earlier completion per day).

### B2 · Server-checked daily + leaderboards
The server sends one day at a time, without answers; submissions are checked on the server with the same answer data. This also closes the "answers in the data file" gap. Daily leaderboard by puzzle number, open 48 hours.

### B3 · Friends & groups
Friend codes, small private groups, group leaderboard.

---

## 7. Track C — Head-to-head battles

### C1 · Battle design spec
Written before any battle code. Starting point: **challenge a friend (async)**: play a practice-style set, send a link, they play the identical set, both see the comparison. **Live duel**, then **mathlete rounds** (sprint, target, countdown). The bonus puzzle pool is a natural source for tiebreakers.

### C2 · Async challenges · C3 · Live rooms

---

## 8. Staffing & status

| Phase | Status | Completed | Notes |
|---|---|---|---|
| Prototype v1 | ✅ superseded | 2026-10-05 | Generated problems on the fly |
| A0 | ✅ | 2026-10-10 | Inside v2 |
| A1 | ✅ | 2026-10-10 | Python engine + harness |
| A2 | ✅ v1 (71 templates) | 2026-10-10 | Grow to 100+ |
| A3 | ✅ | 2026-10-10 | Dataset through 2027-10-31 |
| A4 | 🔶 partly | — | Stats, how-to-play, a11y open |
| P0 | ⬜ open | — | Repo + CI |
| P1 | ✅ live on workers.dev | 2026-10-12 | Custom domain still open (#4) |
| A5 | ⬜ blocked on owner #5 | — | |
| B1–B3 | ⬜ deferred | — | No accounts for now |
| C1–C3 | ⬜ blocked on B2 | — | |

✅ done and verified · 🔶 partly done · ⬜ open (blocker named)

---

## 9. Owner decisions

1. ~~Set size~~ — **decided 2026-10-10:** 5 problems a day, 7 on Saturdays, random bonus puzzle on ~30% of other days.
2. ~~Name~~ — **decided 2026-10-12:** **Molver** (mole + solver), with an original mole mascot. Domain: **molver.net** (molver.com has been held by someone else since 2009). Replaced "Back of the Envelope": the user wanted a short, Wordle-style name. Parked idea from the old name: an occasional Fermi-style "estimate it" bonus that accepts answers within 10%.
3. ~~Hosting~~ — **decided 2026-10-12:** Cloudflare Workers (static assets) deployed from GitHub. Chosen for free static hosting with commercial use allowed and a path to server-checked answers (Workers), leaderboards (D1) and live battles (Durable Objects) on one platform.
4. ~~Domain~~ — **decided 2026-10-12:** molver.net, attached to the daily-math Worker in Cloudflare.
5. **Analytics** vendor (privacy-friendly, no cookies preferred).
6. **Launch date** — what counts as No. 1. Currently 2026-10-05.
7. **Backend/auth** vendor for B1 (deferred).
8. **New puzzle time.** Local midnight (current) or a fixed time for everyone.
9. **Money.** Not needed until after B2.
10. **When solutions open.** Current: the answer shows after two misses; the worked solution opens the next day (`unlock: 'next-day'`, reconfirmed 2026-10-12). Built-in alternatives: `'after-share'` (send your result to open today's answers) or `'immediate'`. Other ideas: open after X hours, or after a friend also finishes.
11. **Bonus rate.** Currently ~30% of non-Saturday days (about 2 a week). Could be fixed days instead (e.g. every Wednesday).

---

## 10. Completion ledger

*Newest first.*

**2026-10-12 · Chalkboard redesign**
- Completed: envelope look replaced with a framed classroom chalkboard (slate board, wood frame, chalk tray with chalk and eraser); chalk display face for the name and headings, chalk handwriting for labels, date and worked steps, a highly legible face for the problem text; colored chalk for state (yellow now, green right, pink missed, blue bonus); Molver the mole sits on the chalk tray and reacts (calm, happy on a right answer, "oops" on a miss); chalk work area with Erase.
- Verification: full play-through test (no errors), phone layout with no sideways scroll, preview with real fonts checked in Chrome.

**2026-10-12 · Renamed to Molver**
- Completed: site, share text, link preview, icon and docs renamed; original mole mascot (header; happy or calm next to the final score); loading and wax-seal copy updated. Saved progress and streaks are kept (storage keys unchanged).
- molver.net attached in Cloudflare; share text and `og:url` now use https://molver.net.

**2026-10-12 · Two tries per problem**
- Completed: two tries per problem (daily, bonus, practice); answer shown after the second miss; 🟨 for second-try solves in the share grid; a pending first try survives a reload.
- Verification: headless-browser test of first-try, second-try and double-miss paths, reload mid-problem, share grid, sealed summary, past solutions, practice and bonus: no errors.

**2026-10-12 · Live on Cloudflare**
- Completed: source of truth moved to `~/daily_math` on Dong's Mac; private GitHub repo `dongfeng2015/daily_math`; Cloudflare Workers deploy from `main`; standalone page head (charset, viewport, link preview, icon); share text now links to the site.
- Verification: headless-browser play-through of the standalone page served without a charset header; live site checked in Chrome (No. 8 loads, puzzles.json 200, UTF-8).
- Next: run the one-time `git init`/`git reset origin/main` in `~/daily_math` so the Mac folder tracks the repo; pick a domain.

**2026-10-10 · v2: a year of pre-built puzzles, sealed solutions, SMS share**
- Completed: Python engine (A1), 71 templates (A2), year scheduler (A3), app v2 with sealed solutions, yesterday's solutions archive, Saturday Seven, bonus puzzles, Text it / Share / Copy, practice pool, timer pause on hidden tab (A0).
- Verification: harness 71 templates × 10,000 seeds, 0 failing cases; build_dataset validated all 2,072 + 107 + 300 practice problems; independent reviewer re-solved samples of every template; headless-browser play-through (Saturday on a phone in dark mode, weekday + bonus on desktop in light mode, yesterday's solutions, practice, end-of-file fallback): no errors.
- Artifacts updated: `back-of-the-envelope.html`, `data/puzzles.json`, `data/puzzles-review.csv`, `engine/*`, `README.md`, this plan.
- Decisions: dataset pre-generated for the year; no accounts for now; share by text; solutions sealed until next day.
- Next: owner reads some of the review CSV; P0 repo; decisions #2–#6, #10.

**2026-10-07 · Plan created**
- Completed: this plan; folder scaffold.

**2026-10-05 · Prototype**
- Completed: single-file playable prototype with 24 templates generated on the fly.

---

## Summary

Molver is a once-a-day set of ACT/SAT-style word problems (five on weekdays, seven on Saturdays, sometimes a bonus puzzle), typed answers, timed, streaked and shared by text like early Wordle. As of 2026-10-10 the whole year through Oct 2027 is pre-built and checked, and solutions stay sealed until the next day so people talk it over. Next: put it in a repo with CI, pick hosting and a domain, grow the template library, and calibrate difficulty with real players before accounts, leaderboards and battles.
