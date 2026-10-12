# Molver — daily math

app/index.html          the web app (loads puzzles.json from the same folder); this folder is what gets deployed
app/puzzles.json        a year of daily sets (copy of data/puzzles.json)
data/puzzles.json       2026-10-05 → 2027-10-31: 392 days, 2,072 problems, 107 bonus days, 60 practice sets
data/puzzles-review.csv one row per problem: date, question, answer, explanation (for reading/editing)
engine/                 how the dataset is made
  engine.py             template contract, number formatting, answer tolerance, validation rules
  STYLE.md              writing rules for problem templates
  templates_*.py        71 templates (12 per tier + 12 bonus puzzles; 11 in tier 4)
  harness.py            python3 harness.py templates_t12 --seeds 10000   (checks every template)
  build_dataset.py      python3 build_dataset.py --start 2026-10-05 --end 2027-10-31 --out ../data

Rebuild after editing templates:
  cd engine && python3 harness.py templates_ref templates_t12 templates_t34 templates_t5b --seeds 10000 \
    && python3 build_dataset.py && cp ../data/puzzles.json ../app/

App settings (top of the script in app/index.html):
  unlock:   'next-day' (default) | 'after-share' | 'immediate'
  shareUrl: added to the share text once the site has a domain

Hosting (Cloudflare Workers, static assets) — live at https://molver.net
  wrangler.jsonc serves ./app as a static site. The GitHub repo is connected to Cloudflare
  (Workers & Pages -> Import a repository), so every push to main deploys automatically.
  Deploy command: npx wrangler deploy      Build command: (none)
  Preview locally: cd app && python3 -m http.server 8000   then open http://localhost:8000

Source of truth: this folder (~/daily_math). The copy in the Claude Project is a snapshot.
The Claude artifact preview is made from app/index.html without its <head> (Claude adds its own).
