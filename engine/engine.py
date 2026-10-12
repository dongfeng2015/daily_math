"""Molver problem engine.

Every problem comes from a *template*: a class with three static methods.

    params(r)  -> dict   draw the numbers, names and context with the seeded Rng `r`.
                         Raise Retry() if a draw is bad; the engine redraws (max 200 times),
                         then falls back to the class attribute `fallback` (a hand-checked dict).
    solve(p)   -> value  the answer, computed on its own from the params (the "oracle").
                         money -> int cents; int -> int; dec/pct/frac -> Fraction (pct is the
                         percent number, e.g. Fraction(25) for 25%).
    render(p)  -> dict   {stem, ask, steps, table?, unit?}. `steps` is the worked solution and
                         must compute its own numbers; its LAST step must contain the answer
                         formatted with the same helper the engine uses (usd / num / frac / pct).

Register with the @template(...) decorator. See harness.py for every rule that is checked.
"""
from __future__ import annotations

import hashlib
import math
import random
import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F

TIER_NAMES = {1: 'Warm-up', 2: 'Everyday', 3: 'Two-step', 4: 'Tricky', 5: 'Stretch', 6: 'Bonus'}
TOPICS = {'money', 'percent', 'rates', 'ratio', 'time', 'averages', 'geometry', 'probability',
          'counting', 'growth', 'algebra', 'data', 'units', 'puzzle'}
KINDS = {'money', 'int', 'dec', 'frac', 'pct'}

REGISTRY: dict[str, type] = {}


class Retry(Exception):
    """Raise inside params() to throw away a bad draw."""


# ---------------------------------------------------------------- people
@dataclass(frozen=True)
class Person:
    name: str
    he: str
    him: str
    his: str

    @property
    def He(self): return self.he.capitalize()

    @property
    def His(self): return self.his.capitalize()

    def __str__(self): return self.name

    def __format__(self, spec): return format(self.name, spec)


_F = ('she', 'her', 'her')
_M = ('he', 'him', 'his')
_NAMES = [
    ('Rosa', _F), ('Luis', _M), ('Priya', _F), ('Sam', _M), ('Jordan', _M), ('Aiyana', _F),
    ('Theo', _M), ('Grace', _F), ('Omar', _M), ('Kenji', _M), ('Dev', _M), ('Maya', _F),
    ('Nadia', _F), ('Marcus', _M), ('Elena', _F), ('Andre', _M), ('Hana', _F), ('Felix', _M),
    ('Zoe', _F), ('Tariq', _M), ('Lucia', _F), ('Ben', _M), ('Imani', _F), ('Diego', _M),
    ('Mei', _F), ('Caleb', _M), ('Sofia', _F), ('Ravi', _M), ('Chloe', _F), ('Malik', _M),
    ('Ava', _F), ('Jamal', _M), ('Ingrid', _F), ('Mateo', _M), ('Leah', _F), ('Wes', _M),
    ('Yuki', _F), ('Owen', _M), ('Fatima', _F), ('Nico', _M), ('Ruth', _F), ('Hugo', _M),
    ('Amara', _F), ('Eli', _M), ('Tess', _F), ('Kofi', _M), ('Jade', _F), ('Arjun', _M),
    ('Carmen', _F), ('Isaac', _M), ('Lena', _F), ('Raul', _M), ('June', _F), ('Silas', _M),
    ('Noor', _F), ('Victor', _M), ('Esme', _F), ('Dmitri', _M), ('Paige', _F), ('Ezra', _M),
]
PEOPLE = [Person(n, *pr) for n, pr in _NAMES]
_BY_NAME = {p.name: p for p in PEOPLE}


def person(name: str) -> Person:
    """Look up a Person by name (use in `fallback` dicts)."""
    return _BY_NAME[name]


# ---------------------------------------------------------------- rng
class Rng:
    def __init__(self, seed: str, used_names: set | None = None):
        h = int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16)
        self._r = random.Random(h)
        self.used = used_names if used_names is not None else set()

    def int(self, a: int, b: int) -> int: return self._r.randint(a, b)
    def pick(self, seq): return self._r.choice(list(seq))
    def sample(self, seq, k): return self._r.sample(list(seq), k)
    def shuffle(self, seq): l = list(seq); self._r.shuffle(l); return l
    def chance(self, p: float) -> bool: return self._r.random() < p
    def random(self) -> float: return self._r.random()

    def person(self) -> Person:
        """A person whose name hasn't been used elsewhere in today's set."""
        free = [p for p in PEOPLE if p.name not in self.used] or PEOPLE
        p = self._r.choice(free)
        self.used.add(p.name)
        return p

    def people(self, k: int) -> list[Person]:
        return [self.person() for _ in range(k)]


# ---------------------------------------------------------------- formatting
def _q(x, dp):
    x = F(x)
    d = Decimal(x.numerator) / Decimal(x.denominator)
    return d.quantize(Decimal(1).scaleb(-dp), rounding=ROUND_HALF_UP)


def num(x, dp: int = 4) -> str:
    """12500 -> '12,500'; Fraction(5,2) -> '2.5'; 1/3 -> '0.3333'. Commas for thousands."""
    x = F(x)
    if x.denominator == 1:
        return f"{x.numerator:,}"
    s = f"{_q(x, dp):,f}"
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return s


def usd(cents: int) -> str:
    """1250 -> '$12.50'; 1200 -> '$12'; 123456 -> '$1,234.56'."""
    assert int(cents) == cents, cents
    cents = int(cents)
    sign = '-' if cents < 0 else ''
    c = abs(cents)
    if c % 100 == 0:
        return f"{sign}${c // 100:,}"
    return f"{sign}${c // 100:,}.{c % 100:02d}"


def usd2(cents: int) -> str:
    """Always two decimals: 1200 -> '$12.00'."""
    cents = int(cents)
    return f"${cents // 100:,}.{cents % 100:02d}"


def frac(x) -> str:
    """Fraction(3,8) -> '3/8'; Fraction(4) -> '4'."""
    x = F(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def mixed(x) -> str:
    """Fraction(11,8) -> '1 3/8'."""
    x = F(x)
    if x.denominator == 1:
        return str(x.numerator)
    w, r = divmod(x.numerator, x.denominator)
    return f"{w} {r}/{x.denominator}" if w else f"{r}/{x.denominator}"


def pct(x) -> str:
    """Fraction(25) -> '25%'; Fraction(25,2) -> '12.5%'."""
    return num(x) + '%'


def clock(minutes: int) -> str:
    """Minutes after midnight -> '9:05 a.m.'"""
    minutes %= 24 * 60
    h, m = divmod(minutes, 60)
    return f"{h % 12 or 12}:{m:02d} {'a.m.' if h < 12 else 'p.m.'}"


def plural(n, one: str, many: str | None = None) -> str:
    return f"{num(n)} {one if n == 1 else (many or one + 's')}"


_WORDS = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty'.split()


def word(n: int) -> str:
    return _WORDS[n] if 0 <= n <= 20 else num(n)


def cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def a_an(n) -> str:
    """Article for a number read aloud: a_an(85) -> 'an 85', a_an(90) -> 'a 90'."""
    t = num(n)
    d = t.replace(',', '')
    an = d.startswith('8') or d in ('11', '18') or re.match(r'^1[18]\d{3}$', d) or re.match(r'^1[18],', t)
    return ('an ' if an else 'a ') + t


def ordinal(n: int) -> str:
    suf = 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suf}"


# ---------------------------------------------------------------- registry
def template(id: str, tier: int, topic: str, kind: str, unit: str | None = None, seconds: int = 60):
    assert tier in TIER_NAMES, tier
    assert topic in TOPICS, topic
    assert kind in KINDS, kind

    def deco(cls):
        assert id not in REGISTRY, f"duplicate template id {id}"
        cls.id, cls.tier, cls.topic, cls.kind, cls.unit, cls.seconds = id, tier, topic, kind, unit, seconds
        for m in ('params', 'solve', 'render'):
            assert hasattr(cls, m), f"{id} missing {m}()"
        assert hasattr(cls, 'fallback'), f"{id} missing fallback"
        REGISTRY[id] = cls
        return cls
    return deco


# ---------------------------------------------------------------- answers
def core(kind: str, value) -> str:
    """The answer as it must appear in the last worked step."""
    if kind == 'money':
        return usd(value)
    if kind == 'pct':
        return pct(value)
    if kind == 'frac':
        return frac(value)
    return num(value)


def tolerance(kind: str, v: F) -> float:
    if kind == 'money' or kind == 'int':
        return 0.0051 if kind == 'money' else 1e-9
    if kind in ('dec', 'pct'):
        return 1e-6 if (v * 100).denominator == 1 else 0.005 + 1e-9
    return max(0.0005, abs(float(v)) * 0.003)  # frac: equivalent fraction or a close decimal


def build(cls, seed: str, used_names: set | None = None, force_fallback: bool = False) -> dict:
    r = Rng(seed, used_names)
    p = None
    if not force_fallback:
        for _ in range(200):
            try:
                p = cls.params(r)
                break
            except Retry:
                continue
    if p is None:
        p = cls.fallback
    value = cls.solve(p)
    out = cls.render(p)
    unit = out.get('unit', cls.unit)
    kind = cls.kind
    if kind == 'money':
        assert F(value).denominator == 1, f"{cls.id}: money must be whole cents, got {value}"
        value = int(value)
        ans_value = value / 100
    elif kind == 'int':
        assert F(value).denominator == 1, f"{cls.id}: int answer not whole: {value}"
        value = int(value)
        ans_value = value
    else:
        value = F(value)
        ans_value = float(value)
    c = core(kind, value)
    display = c if kind in ('money', 'pct') else (c + (f" {unit}" if unit else ''))
    if kind == 'frac' and F(value).denominator > 1 and value > 1:
        display = f"{c} ({mixed(value)}){(' ' + unit) if unit else ''}"
    answer = {'kind': kind, 'value': round(ans_value, 10),
              'tol': tolerance(kind, F(value) / (100 if kind == 'money' else 1))}
    if kind == 'frac':
        answer['frac'] = [F(value).numerator, F(value).denominator]
    prob = {
        'templateId': cls.id, 'tier': cls.tier, 'tierName': TIER_NAMES[cls.tier], 'topic': cls.topic,
        'stem': out['stem'].strip(), 'ask': out['ask'].strip(),
        'answer': answer, 'unit': None if kind in ('money', 'pct') else unit,
        'display': display, 'core': c, 'steps': [s.strip() for s in out['steps']],
        'seconds': cls.seconds,
    }
    if out.get('table'):
        prob['table'] = out['table']
    return prob


# ---------------------------------------------------------------- validation
WORDS_RANGE = {1: (20, 75), 2: (35, 125), 3: (35, 125), 4: (35, 125), 5: (30, 125), 6: (20, 125)}
_BAD = re.compile(r'None|nan|NaN|inf\b|Infinity|\[object|\{|\}|  | ,| \.(?!\d)|\.\.(?!\.)')
_NUM = re.compile(r'\d[\d,]*(?:\.\d+)?')


def _sig_digits(tok: str) -> int:
    t = tok.replace(',', '')
    if '.' in t:
        d = t.replace('.', '').lstrip('0')
    else:
        d = t.lstrip('0').rstrip('0')
    return len(d)


def word_count(prob: dict) -> int:
    return len((prob['stem'] + ' ' + prob['ask']).split())


def validate(prob: dict) -> list[str]:
    e = []
    texts = [prob['stem'], prob['ask'], prob['display'], *prob['steps']]
    if prob.get('table'):
        t = prob['table']
        if not t.get('headers') or not t.get('rows'):
            e.append('table needs headers and rows')
        else:
            for row in t['rows']:
                if len(row) != len(t['headers']):
                    e.append('table row length mismatch')
            texts += [str(x) for x in t['headers']] + [str(x) for row in t['rows'] for x in row]
    for s in texts:
        m = _BAD.search(s)
        if m:
            e.append(f"bad text {m.group(0)!r} in: {s[:80]}")
    if not prob['ask'].endswith('?'):
        e.append('ask must end with ?')
    if prob['ask'].count('?') != 1:
        e.append('ask must be one question')
    lo, hi = WORDS_RANGE[prob['tier']]
    wc = word_count(prob)
    if not lo <= wc <= hi:
        e.append(f"word count {wc} outside {lo}-{hi}")
    if not 2 <= len(prob['steps']) <= 6:
        e.append(f"{len(prob['steps'])} steps; need 2-6")
    if prob['core'] not in prob['steps'][-1]:
        e.append(f"last step must contain answer {prob['core']!r}: {prob['steps'][-1]}")
    a = prob['answer']
    if not a['value'] > 0:
        e.append(f"answer must be positive: {a['value']}")
    if a['kind'] in ('dec', 'pct'):
        v = F(a['value']).limit_denominator(10**6)
        if (v * 1000).denominator != 1 and not re.search(r'nearest|round', prob['ask'], re.I):
            e.append(f"decimal answer {a['value']} needs more than 3 places; say how to round in the ask")
    if a['kind'] == 'frac' and a['frac'][1] > 1000:
        e.append('fraction denominator too large')
    for tok in _NUM.findall(prob['stem'] + ' ' + prob['ask']):
        if _sig_digits(tok) > 5:
            e.append(f"operand {tok} has more than 5 significant digits")
    return e
