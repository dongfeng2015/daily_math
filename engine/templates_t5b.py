"""Tier 5 (Stretch) and Bonus (tier 6, classic puzzle) templates, set B."""
import itertools
from fractions import Fraction as F

from engine import Retry, template, person, usd, num, frac, plural, word, cap, ordinal, a_an

SUP = {2: '²', 3: '³', 4: '⁴', 5: '⁵', 6: '⁶'}
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def times(m):
    """2 -> 'twice', 3 -> 'three times'."""
    return 'twice' if m == 2 else f"{word(m)} times"


def cx(c, v='x'):
    """Coefficient times a variable: 1 -> 'x', 3 -> '3x'."""
    return v if c == 1 else f"{c}{v}"


def chain(n):
    """5 -> '5 × 4 × 3 × 2 × 1'."""
    return ' × '.join(str(i) for i in range(n, 0, -1))


def fact(n):
    out = 1
    for i in range(2, n + 1):
        out *= i
    return out


def join_and(items, conj='and'):
    items = list(items)
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} {conj} {items[1]}"
    return ', '.join(items[:-1]) + f" {conj} " + items[-1]


# =====================================================================================
# TIER 5
# =====================================================================================

@template(id='t5.same-kind-two-draws.v1', tier=5, topic='probability', kind='frac', seconds=120)
class SameKindTwoDraws:
    # (setup, action, plural noun, kind A, kind B, attribute word, irrelevant detail, x range)
    CONTEXTS = [
        ("{w} keeps a tin of cookies on {his} desk. It holds {a} chocolate chip cookies and {b} oatmeal "
         "cookies, all the same size.",
         "Without looking, {he} takes out two cookies, one after the other, and doesn't put either back.",
         'cookies', 'chocolate chip', 'oatmeal', 'kind', "The tin was a gift from {his} neighbor {x} years ago.",
         (2, 9)),
        ("{w} packed a cooler for a beach day with {a} bottles of lemonade and {b} bottles of iced tea.",
         "Later, {he} reaches into the ice without looking and pulls out two bottles, one after the other.",
         'bottles', 'lemonade', 'iced tea', 'drink', "The beach is {x} miles from {his} apartment.", (8, 35)),
        ("{w}'s board game comes with a cloth bag holding {a} red tokens and {b} yellow tokens.",
         "To start the game, {he} draws two tokens at random without putting the first one back.",
         'tokens', 'red', 'yellow', 'color', "The box says the game is for ages {x} and up.", (8, 12)),
        ("A fruit bowl in {w}'s kitchen holds {a} red apples and {b} green apples.",
         "On {his} way out the door, {he} grabs two apples at random, one after the other.",
         'apples', 'red', 'green', 'color', "{He} bought them at a farm stand that opened {x} years ago.",
         (10, 40)),
    ]

    @staticmethod
    def params(r):
        a, b = r.int(3, 9), r.int(3, 9)
        if a == b:
            raise Retry
        ctx = r.pick(SameKindTwoDraws.CONTEXTS)
        x = r.int(*ctx[7])
        if x in (a, b, a + b):
            raise Retry
        return dict(who=r.person(), ctx=ctx, a=a, b=b, x=x)

    fallback = dict(who=person('Rosa'), ctx=CONTEXTS[0], a=5, b=3, x=4)

    @staticmethod
    def solve(p):
        items = ['A'] * p['a'] + ['B'] * p['b']
        pairs = [(i, j) for i in range(len(items)) for j in range(len(items)) if i != j]
        same = sum(1 for i, j in pairs if items[i] == items[j])
        return F(same, len(pairs))

    @staticmethod
    def render(p):
        w, a, b = p['who'], p['a'], p['b']
        setup, act, noun, ka, kb, attr, irr, _ = p['ctx']
        f = dict(w=w, he=w.he, He=w.He, his=w.his, a=a, b=b, x=p['x'])
        stem = f"{setup.format(**f)} {irr.format(**f)} {act.format(**f)}"
        n = a + b
        den = n * (n - 1)
        tot = a * (a - 1) + b * (b - 1)
        last = f"Add the two cases: {a * (a - 1)}/{den} + {b * (b - 1)}/{den} = {tot}/{den}"
        last += f" = {frac(F(tot, den))}." if F(tot, den).denominator != den else "."
        steps = [
            f"There are {a} + {b} = {n} {noun} in all.",
            f"P(both {ka}) = {a}/{n} × {a - 1}/{n - 1} = {a * (a - 1)}/{den}.",
            f"P(both {kb}) = {b}/{n} × {b - 1}/{n - 1} = {b * (b - 1)}/{den}.",
            last,
        ]
        ask = f"What is the probability, as a fraction, that both {noun} are the same {attr}?"
        return dict(stem=stem, ask=ask, steps=steps)


@template(id='t5.ages-times-as-old.v1', tier=5, topic='algebra', kind='int', unit='years', seconds=120)
class AgesTimesAsOld:
    # role: (k range, older-age range, (word for a boy, word for a girl))
    ROLES = {
        'parent': ((3, 6), (26, 50), ('son', 'daughter')),
        'grandparent': ((5, 11), (55, 84), ('grandson', 'granddaughter')),
        'aunt': ((2, 5), (22, 48), ('nephew', 'niece')),
    }
    IRR = [
        "Every summer the two of them go fishing at a lake {x} miles from home.",
        "This spring they planted {x} tomato plants together.",
        "They live {x} blocks apart and walk together most weekends.",
    ]

    @staticmethod
    def params(r):
        o, y = r.people(2)
        role = r.pick(sorted(AgesTimesAsOld.ROLES))
        (k0, k1), (lo, hi), _ = AgesTimesAsOld.ROLES[role]
        k, c = r.int(k0, k1), r.int(2, 30)
        if not lo <= k * c <= hi:
            raise Retry
        var = r.pick(['future', 'past'])
        if var == 'future':
            if k < 3:
                raise Retry
            m = r.int(2, k - 1)
            top = c * (k - m)
        else:
            m = r.int(k + 1, k + 6)
            top = c * (m - k)
        if top % (m - 1):
            raise Retry
        n = top // (m - 1)
        if not 1 <= n <= 30 or (var == 'past' and n >= c) or (var == 'future' and n < 2):
            raise Retry
        ask_old = r.chance(0.4)
        ans = k * c if ask_old else c
        x = r.int(3, 25)
        if ans in (n, x) or x == n:
            raise Retry
        return dict(o=o, y=y, role=role, k=k, c=c, m=m, n=n, var=var, ask_old=ask_old,
                    irr=r.pick(AgesTimesAsOld.IRR), x=x)

    fallback = dict(o=person('Marcus'), y=person('Maya'), role='parent', k=4, c=8, m=2, n=16, var='future',
                    ask_old=False, irr=IRR[0], x=12)

    @staticmethod
    def solve(p):
        k, m, n = p['k'], p['m'], p['n']
        for x in range(1, 121):
            if p['var'] == 'future' and k * x + n == m * (x + n):
                return k * x if p['ask_old'] else x
            if p['var'] == 'past' and x > n and k * x - n == m * (x - n):
                return k * x if p['ask_old'] else x
        raise ValueError('no age fits')

    @staticmethod
    def render(p):
        o, y, k, c, m, n = p['o'], p['y'], p['k'], p['c'], p['m'], p['n']
        rel = AgesTimesAsOld.ROLES[p['role']][2][0 if y.he == 'he' else 1]
        first = f"{o} is {times(k)} as old as {o.his} {rel}, {y}."
        irr = p['irr'].format(x=p['x'])
        if p['var'] == 'future':
            second = f"In {plural(n, 'year')}, {o} will be {times(m)} as old as {y}."
            eq = f"In {plural(n, 'year')}: {k}x + {n} = {m}(x + {n}) = {m}x + {m * n}."
            if k - m == 1:
                solve_line = f"Subtract {m}x and {n} from both sides: x = {m * n} − {n} = {c}."
            else:
                solve_line = f"Subtract {m}x and {n} from both sides: {k - m}x = {m * n} − {n} = {(m - 1) * n}, so x = {c}."
            check = f"Check: in {plural(n, 'year')}, {k * c + n} = {m} × {c + n}."
        else:
            second = f"Exactly {plural(n, 'year')} ago, {o} was {times(m)} as old as {y}."
            eq = f"{plural(n, 'year')} ago: {k}x − {n} = {m}(x − {n}) = {m}x − {m * n}."
            if m - k == 1:
                solve_line = f"Move the x terms to one side: x = {m * n} − {n} = {c}."
            else:
                solve_line = f"Move the x terms to one side: {m - k}x = {m * n} − {n} = {(m - 1) * n}, so x = {c}."
            check = f"Check: {plural(n, 'year')} ago, {k * c - n} = {m} × {c - n}."
        stem = f"{first} {irr} {second}"
        target = o if p['ask_old'] else y
        steps = [f"Let {y}'s age now be x, so {o} is {k}x.", eq, solve_line]
        if p['ask_old']:
            steps.append(f"So {o} is {k} × {c} = {k * c} years old now. {check}")
        else:
            steps.append(f"So {y} is {c} years old now. {check}")
        return dict(stem=stem, ask=f"How old is {target} now, in years?", steps=steps)


@template(id='t5.clock-hands-angle.v1', tier=5, topic='geometry', kind='dec', unit='degrees', seconds=110)
class ClockHandsAngle:
    CONTEXTS = [
        ("{w} glances at the clock above the classroom door during a math quiz. It reads {t}, and the quiz "
         "started {x} minutes earlier.", (10, 25)),
        ("The clock at the train station has a face {x} feet across. While {w} waits on the platform, it "
         "reads {t}.", (3, 6)),
        ("{w} slides a tray of muffins into the oven when the kitchen clock reads {t}. The recipe says to bake "
         "them for {x} minutes.", (18, 25)),
        ("{w} snaps a photo of the clock tower in the town square at exactly {t}. The tower is {x} feet tall.",
         (60, 95)),
    ]

    @staticmethod
    def params(r):
        h, m = r.int(1, 12), r.int(1, 59)
        ang = abs(30 * (h % 12) * 2 - 11 * m)  # in half-degrees
        ang %= 720
        ang = min(ang, 720 - ang)
        if ang == 0:
            raise Retry
        ctx = r.pick(ClockHandsAngle.CONTEXTS)
        return dict(who=r.person(), ctx=ctx, h=h, m=m, x=r.int(*ctx[1]))

    fallback = dict(who=person('Omar'), ctx=CONTEXTS[0], h=3, m=40, x=15)

    @staticmethod
    def solve(p):
        # each hand as a fraction of a full turn
        minute = F(p['m'], 60)
        hour = (F(p['h'] % 12) + F(p['m'], 60)) / 12
        d = abs(minute - hour) * 360
        return min(d, 360 - d)

    @staticmethod
    def render(p):
        w, h, m = p['who'], p['h'], p['m']
        t = f"{h}:{m:02d}"
        stem = (p['ctx'][0].format(w=w, t=t, x=p['x']) +
                " As on any ordinary clock, the hour hand moves steadily from one number toward the next as the "
                "minutes pass.")
        mm = 6 * m
        hh = 30 * (h % 12) + F(m, 2)
        steps = [f"The minute hand moves 6 degrees per minute: {m} × 6 = {mm} degrees past the 12."]
        if h == 12:
            steps.append(f"The hour hand moves 0.5 degree per minute, starting at the 12: {m} × 0.5 = {num(hh)} "
                         f"degrees past the 12.")
        else:
            steps.append(f"The hour hand is 30 degrees per hour plus 0.5 degree per minute: {h} × 30 + {m} × 0.5 = "
                         f"{num(hh)} degrees past the 12.")
        d = abs(hh - mm)
        steps.append(f"The gap between them: {num(max(hh, mm))} − {num(min(hh, mm))} = {num(d)} degrees.")
        if d > 180:
            steps.append(f"That's more than 180, so the smaller angle is 360 − {num(d)} = {num(360 - d)} degrees.")
        else:
            steps.append(f"That's not more than 180, so the smaller angle is {num(d)} degrees.")
        return dict(stem=stem, ask="What is the smaller angle between the hour hand and the minute hand, in degrees?",
                    steps=steps)


@template(id='t5.league-or-menu-count.v1', tier=5, topic='counting', kind='int', unit='games', seconds=100)
class LeagueOrMenuCount:
    # league: (sport, members, game word)
    LEAGUES = [('volleyball', 'team', 'teams', 'game', 'games'), ('kickball', 'team', 'teams', 'game', 'games'),
               ('chess', 'player', 'players', 'match', 'matches'),
               ('table tennis', 'player', 'players', 'match', 'matches')]
    # menu: (shop, item, items, choice word, base word, base options, irrelevant)
    MENUS = [
        ('pizza shop', 'pizza', 'pizzas', 'toppings', 'crusts', ['thin', 'regular', 'deep-dish'],
         "A large pizza is cut into {x} slices."),
        ('burrito stand', 'burrito bowl', 'burrito bowls', 'fillings', 'bases',
         ['white rice', 'brown rice', 'greens'], "The stand serves about {x} bowls on a busy day."),
        ('ice cream stand', 'sundae', 'sundaes', 'toppings', 'ice cream flavors',
         ['vanilla', 'chocolate', 'strawberry'], "Each sundae comes in a {x}-ounce cup."),
    ]

    @staticmethod
    def params(r):
        if r.chance(0.5):
            n, g = r.int(6, 12), r.pick([1, 2, 2])
            return dict(var='league', who=r.person(), lg=r.pick(LeagueOrMenuCount.LEAGUES), n=n, g=g,
                        x=r.pick([30, 40, 45, 50]))
        k = r.pick([2, 3])
        n = r.int(6, 12) if k == 2 else r.int(6, 9)
        c = r.int(2, 3)
        menu = r.pick(LeagueOrMenuCount.MENUS)
        x = r.pick([6, 8, 10, 12]) if menu[0] == 'pizza shop' else r.pick([150, 200, 250, 300]) \
            if menu[0] == 'burrito stand' else r.pick([10, 12, 16])
        return dict(var='menu', who=r.person(), menu=menu, n=n, k=k, c=c, x=x)

    fallback = dict(var='league', who=person('Grace'), lg=LEAGUES[0], n=8, g=2, x=40)

    @staticmethod
    def solve(p):
        if p['var'] == 'league':
            return sum(1 for _ in itertools.combinations(range(p['n']), 2)) * p['g']
        return sum(1 for _ in itertools.combinations(range(p['n']), p['k'])) * p['c']

    @staticmethod
    def render(p):
        w = p['who']
        if p['var'] == 'league':
            sport, one, many, game, games = p['lg']
            n, g = p['n'], p['g']
            pairs = n * (n - 1) // 2
            stem = (f"{w} is organizing a {sport} league with {n} {many} this season. Every {one} will play every "
                    f"other {one} exactly {'once' if g == 1 else 'twice'} during the regular season. Each {game} "
                    f"takes about {p['x']} minutes.")
            steps = [f"Each {game} is a pair of {many}. Each of the {n} {many} pairs with {n - 1} others: "
                     f"{n} × {n - 1} = {n * (n - 1)}.",
                     f"That counts every pair twice, so divide by 2: {n * (n - 1)} ÷ 2 = {pairs} pairs."]
            if g == 2:
                steps.append(f"Each pair plays twice: {pairs} × 2 = {pairs * 2} {games}.")
            else:
                steps.append(f"Each pair plays once, so there are {pairs} {games}.")
            return dict(stem=stem, ask=f"How many {games} will be played in the regular season?", steps=steps,
                        unit=games)
        shop, item, items, ch, base, opts, irr = p['menu']
        n, k, c = p['n'], p['k'], p['c']
        opts = opts[:c]
        sets = fact(n) // fact(k) // fact(n - k)
        stem = (f"At {'an' if shop[0] in 'aeiou' else 'a'} {shop}, customers build a {item} by choosing exactly {k} different {ch} from a list of {n}. "
                f"Every {item} also gets one of {c} {base}: {join_and(opts, 'or')}. {irr.format(x=p['x'])} "
                f"The order the {ch} are chosen in doesn't matter.")
        if k == 2:
            s1 = (f"Pick 2 of {n} {ch}: {n} × {n - 1} = {n * (n - 1)} ordered picks, ÷ 2 because order doesn't "
                  f"matter = {sets} sets.")
        else:
            s1 = (f"Pick 3 of {n} {ch}: {n} × {n - 1} × {n - 2} = {n * (n - 1) * (n - 2)} ordered picks, ÷ 6 "
                  f"(the 3 × 2 × 1 orders of the same three) = {sets} sets.")
        steps = [s1, f"Each set can go with any of the {c} {base}: {sets} × {c} = {sets * c} {items}."]
        return dict(stem=stem, ask=f"How many different {items} can a customer build?", steps=steps, unit=items)


@template(id='t5.at-least-once-complement.v1', tier=5, topic='probability', kind='frac', seconds=110)
class AtLeastOnceComplement:
    @staticmethod
    def params(r):
        var = r.pick(['coin', 'die', 'spinner'])
        w = r.person()
        if var == 'coin':
            return dict(var=var, who=w, s=2, k=1, n=r.int(3, 6), x=r.pick(['6:00', '6:30', '7:00']))
        if var == 'die':
            return dict(var=var, who=w, s=6, k=r.pick([1, 2]), n=r.int(2, 3), x=r.pick([30, 36, 40, 48]))
        s = r.pick([4, 5, 8, 10])
        k = r.int(1, 2) if s < 8 else r.int(1, 3)
        n = r.int(2, 3)
        x = r.int(2, 5)
        if x == n:
            raise Retry
        return dict(var=var, who=w, s=s, k=k, n=n, x=x)

    fallback = dict(var='die', who=person('Theo'), s=6, k=1, n=3, x=40)

    @staticmethod
    def solve(p):
        outcomes = list(itertools.product(range(p['s']), repeat=p['n']))
        good = sum(1 for o in outcomes if any(v < p['k'] for v in o))
        return F(good, len(outcomes))

    @staticmethod
    def render(p):
        w, s, k, n = p['who'], p['s'], p['k'], p['n']
        q = F(s - k, s)
        none = q ** n
        if p['var'] == 'coin':
            stem = (f"{w} and {w.his} brother flip a coin each night to decide who washes the dinner dishes; heads "
                    f"means {w} washes. This week they'll flip for {word(n)} nights in a row. Dinner is usually "
                    f"ready by {p['x']} each evening.")
            ask = f"What is the probability, as a fraction, that {w} washes the dishes at least once in those {n} nights?"
            steps = [f"Work with the opposite: {w} never washes only if every flip is tails. One flip is tails with "
                     f"probability 1/2.",
                     f"Tails all {n} nights: (1/2){SUP[n]} = {frac(none)}.",
                     f"At least one heads: 1 − {frac(none)} = {frac(1 - none)}."]
        elif p['var'] == 'die':
            tgt = 'a 6' if k == 1 else 'a 5 or a 6'
            short = '6' if k == 1 else '5 or 6'
            stem = (f"In a board game, {w}'s piece is stuck in the jail space. Under the house rules, {w.he} rolls a "
                    f"standard six-sided die {word(n)} times, and {w.he} escapes if any roll is {tgt}. The board "
                    f"has {p['x']} spaces in all.")
            ask = f"What is the probability, as a fraction, that {w} escapes?"
            qs = f"{s - k}/{s}" + (f" = {frac(q)}" if q.denominator != s else "")
            steps = [f"Work with the opposite: one roll is not {tgt} with probability {qs}.",
                     f"No {short} in {n} rolls: ({frac(q)}){SUP[n]} = {frac(none)}.",
                     f"At least one {short}: 1 − {frac(none)} = {frac(1 - none)}."]
        else:
            marked = f"{word(k)} of them {'is' if k == 1 else 'are'} marked Prize"
            stem = (f"At the school fair, a spinner has {s} equal sections, and {marked}. {w} trades "
                    f"{p['x']} tickets for {word(n)} spins.")
            ask = f"What is the probability, as a fraction, that {w} lands on Prize at least once?"
            qs = f"{s - k}/{s}" + (f" = {frac(q)}" if q.denominator != s else "")
            steps = [f"Work with the opposite: one spin misses Prize with probability {qs}.",
                     f"All {n} spins miss: ({frac(q)}){SUP[n]} = {frac(none)}.",
                     f"At least one Prize: 1 − {frac(none)} = {frac(1 - none)}."]
        return dict(stem=stem, ask=ask, steps=steps)


@template(id='t5.two-value-count.v1', tier=5, topic='algebra', kind='int', unit='coins', seconds=120)
class TwoValueCount:
    COINS = [('quarter', 'quarters', 25, 'dime', 'dimes', 10), ('quarter', 'quarters', 25, 'nickel', 'nickels', 5),
             ('dime', 'dimes', 10, 'nickel', 'nickels', 5)]
    TICKETS = [(900, 500), (1000, 600), (1200, 700), (800, 500)]

    @staticmethod
    def params(r):
        var = r.pick(['coins', 'tickets', 'stamps'])
        if var == 'coins':
            n = r.int(12, 30)
            types = r.pick(TwoValueCount.COINS)
            x0 = r.int(2, 12)
        elif var == 'tickets':
            n = r.pick(range(40, 151, 2))
            types = r.pick(TwoValueCount.TICKETS)
            x0 = r.int(10, n - 10)
        else:
            n = r.int(12, 30)
            types = (75, 60)
            x0 = r.int(3, min(n - 3, 12))  # keeps the ÷ 15 step within the times table
        hi_count = x0
        if hi_count >= n - 1:
            raise Retry
        ask_hi = r.chance(0.6)
        x = {'coins': r.int(3, 9), 'tickets': r.pick([250, 300, 350, 400]), 'stamps': r.int(4, 9)}[var]
        ans = hi_count if ask_hi else n - hi_count
        p = dict(var=var, who=r.person(), n=n, types=types, hi=hi_count, ask_hi=ask_hi, x=x)
        shown = [str(n), str(x), usd(TwoValueCount.total(p))] + [usd(t) for t in types if isinstance(t, int)]
        if any(str(ans) in t for t in shown):
            raise Retry
        return p

    fallback = dict(var='coins', who=person('Diego'), n=20, types=COINS[0], hi=8, ask_hi=True, x=5)

    @staticmethod
    def _vals(p):
        t = p['types']
        if p['var'] == 'coins':
            return t[2], t[5], t[1], t[4], t[0], t[3]
        if p['var'] == 'tickets':
            return t[0], t[1], 'adult tickets', 'student tickets', 'adult ticket', 'student ticket'
        return 75, 60, 'letter stamps', 'postcard stamps', 'letter stamp', 'postcard stamp'

    @staticmethod
    def total(p):
        hi_v, lo_v = TwoValueCount._vals(p)[:2]
        return p['hi'] * hi_v + (p['n'] - p['hi']) * lo_v

    @staticmethod
    def solve(p):
        hi_v, lo_v = TwoValueCount._vals(p)[:2]
        v = TwoValueCount.total(p)
        hits = [h for h in range(p['n'] + 1) if h * hi_v + (p['n'] - h) * lo_v == v]
        assert len(hits) == 1
        return hits[0] if p['ask_hi'] else p['n'] - hits[0]

    @staticmethod
    def render(p):
        w, n, hc = p['who'], p['n'], p['hi']
        hv, lv, hp, lp, h1, l1 = TwoValueCount._vals(p)
        v = TwoValueCount.total(p)
        if p['var'] == 'tickets':
            fmt = usd
        else:
            def fmt(c):
                return f"{num(c)} cents"
        if p['var'] == 'coins':
            stem = (f"{w} empties the cup holder in {w.his} car and finds nothing but {hp} and {lp}. There are {n} "
                    f"coins in all, worth {usd(v)} together. {w.He} has had the car for {p['x']} years.")
            ask = f"How many {hp if p['ask_hi'] else lp} are in the cup holder?"
        elif p['var'] == 'tickets':
            stem = (f"The drama club at {w}'s school sold {n} tickets for its Saturday show. Adult tickets cost "
                    f"{usd(hv)} and student tickets cost {usd(lv)}. Ticket sales came to {usd(v)} in all, and the "
                    f"auditorium has {p['x']} seats.")
            ask = f"How many {hp if p['ask_hi'] else lp} were sold?"
        else:
            stem = (f"{w} buys {n} stamps at the post office: some 60-cent postcard stamps and some 75-cent letter "
                    f"stamps. {w.He} spends {usd(v)} in all. There are {p['x']} people in line behind {w.him}.")
            ask = f"How many {hp if p['ask_hi'] else lp} does {w} buy?"
        base = n * lv
        extra = v - base
        k = extra // (hv - lv)
        steps = [f"Suppose all {n} were {lp}: {n} × {fmt(lv)} = {fmt(base)}.",
                 f"The real total is {fmt(v)}, which is {fmt(v)} − {fmt(base)} = {fmt(extra)} more.",
                 f"Each {h1} adds {fmt(hv - lv)} more than a {l1}, so there are {fmt(extra)} ÷ {fmt(hv - lv)} = "
                 f"{k} {hp}" + (f" (check: {k} × {fmt(hv - lv)} = {fmt(extra)})." if hv - lv == 15 else ".")]
        if not p['ask_hi']:
            steps.append(f"The rest are {lp}: {n} − {hc} = {n - hc}.")
        unit = hp if p['ask_hi'] else lp
        return dict(stem=stem, ask=ask, steps=steps, unit=unit)


@template(id='t5.survey-two-circles.v1', tier=5, topic='counting', kind='int', unit='people', seconds=100)
class SurveyTwoCircles:
    # (intro, people, row labels X / Y / both / neither, ask phrases (both, neither), irrelevant)
    CONTEXTS = [
        ("A community center asked {S} members which summer trips they would sign up for.", 'members',
         ('Hiking trip', 'Kayaking trip', 'Both trips', 'Neither trip'),
         ('signed up for both trips', 'signed up for neither trip'), "The sign-up sheet was posted for {x} days."),
        ("{w} surveyed all {S} students in {his} grade about pets at home.", 'students',
         ('Has a dog', 'Has a cat', 'Has both', 'Has neither'),
         ('have both a dog and a cat', 'have neither a dog nor a cat'),
         "{He} handed out the surveys during {ax}-minute homeroom."),
        ("A café asked {S} regular customers which drinks they had ordered in the past month.", 'customers',
         ('Iced coffee', 'Hot tea', 'Both drinks', 'Neither drink'),
         ('ordered both drinks', 'ordered neither drink'), "The café has {x} tables."),
    ]

    @staticmethod
    def params(r):
        S = r.pick([40, 48, 50, 60, 64, 75, 80, 90, 100, 120])
        both = r.int(3, S // 6)
        ox, oy = r.int(4, S // 3), r.int(4, S // 3)
        nei = S - both - ox - oy
        if nei < 3:
            raise Retry
        ask = r.pick(['both', 'neither'])
        ans = both if ask == 'both' else nei
        x = r.int(5, 20) if S > 20 else 5
        shown = [ox + both, oy + both, nei if ask == 'both' else both, S, x]
        if ans in shown or len(set(shown)) < len(shown):
            raise Retry
        return dict(who=r.person(), ctx=r.pick(SurveyTwoCircles.CONTEXTS), S=S, both=both, ox=ox, oy=oy, nei=nei,
                    ask=ask, x=x)

    fallback = dict(who=person('Nadia'), ctx=CONTEXTS[1], S=60, both=6, ox=20, oy=14, nei=20, ask='neither', x=12)

    @staticmethod
    def solve(p):
        people = ([(1, 1)] * p['both'] + [(1, 0)] * p['ox'] + [(0, 1)] * p['oy'] + [(0, 0)] * p['nei'])
        assert len(people) == p['S']
        if p['ask'] == 'both':
            return sum(1 for a, b in people if a and b)
        return sum(1 for a, b in people if not a and not b)

    @staticmethod
    def render(p):
        w = p['who']
        intro, folks, labels, phrases, irr = p['ctx']
        S, both, nei = p['S'], p['both'], p['nei']
        A, B = p['ox'] + both, p['oy'] + both
        f = dict(w=w, he=w.he, He=w.He, his=w.his, S=S, x=p['x'], ax=a_an(p['x']))
        stem = (f"{intro.format(**f)} The results are in the table. The \"{labels[0]}\" and \"{labels[1]}\" "
                f"counts include the {folks} who {phrases[0]}. {irr.format(**f)}")
        third = [labels[2], both] if p['ask'] == 'neither' else [labels[3], nei]
        table = dict(headers=['Answer', f"Number of {folks}"], rows=[[labels[0], A], [labels[1], B], third])
        U = S - nei
        if p['ask'] == 'neither':
            steps = [f"Adding {A} + {B} = {A + B} counts the 'both' group twice.",
                     f"At least one: {A + B} − {both} = {U}.",
                     f"Neither: {S} − {U} = {nei}."]
            ask = f"How many of the {S} {folks} {phrases[1]}?"
        else:
            steps = [f"At least one: {S} − {nei} = {U}.",
                     f"Adding {A} + {B} = {A + B} counts the 'both' group twice.",
                     f"So the extra count is the 'both' group: {A + B} − {U} = {both}."]
            ask = f"How many {folks} {phrases[0]}?"
        return dict(stem=stem, ask=ask, steps=steps, table=table, unit=folks)


@template(id='t5.growing-weekly-savings.v1', tier=5, topic='growth', kind='money', seconds=110)
class GrowingWeeklySavings:
    CONTEXTS = [
        ("{w} is saving for a new bike. {He} puts {a} in a jar the first week, and every week after that {he} "
         "puts in {d} more than the week before.", "{He} started the plan on {his} {x} birthday."),
        ("{w} just started a dog-walking business. {He} moves {a} into savings the first week, and each week "
         "after that {he} moves {d} more than the week before.", "{He} has {x} regular customers."),
        ("{w}'s robotics club runs a weekly bake sale. In week 1 the club sets aside {a} for a trip, and each "
         "week after that it sets aside {d} more than the week before.",
         "The club has {x} members this year."),
    ]

    @staticmethod
    def params(r):
        n = r.int(8, 20)
        a = r.int(3, 20) * 100
        d = r.pick([50, 100, 100, 150, 200, 200, 300, 500])
        last = a + (n - 1) * d
        if (a + last) % 100 and n % 2:
            raise Retry
        ci = r.int(0, 2)
        x = ordinal(r.int(12, 16)) if ci == 0 else r.int(3, 9) if ci == 1 else r.int(9, 25)
        return dict(who=r.person(), ci=ci, n=n, a=a, d=d, x=x)

    fallback = dict(who=person('Sam'), ci=0, n=12, a=500, d=200, x='13th')

    @staticmethod
    def solve(p):
        return sum(p['a'] + i * p['d'] for i in range(p['n']))

    @staticmethod
    def render(p):
        w, n, a, d = p['who'], p['n'], p['a'], p['d']
        txt, irr = GrowingWeeklySavings.CONTEXTS[p['ci']]
        f = dict(w=w, he=w.he, He=w.He, his=w.his, a=usd(a), d=usd(d), x=p['x'])
        stem = f"{txt.format(**f)} {irr.format(**f)}"
        who = w if p['ci'] < 2 else 'the club'
        last = a + (n - 1) * d
        steps = [f"Week {n}: {usd(a)} + {n - 1} × {usd(d)} = {usd(last)}.",
                 f"Pair week 1 with week {n}, week 2 with week {n - 1}, and so on: each pair adds to "
                 f"{usd(a)} + {usd(last)} = {usd(a + last)}."]
        total = n * (a + last) // 2
        if n % 2 == 0:
            steps.append(f"{n} weeks make {n // 2} pairs: {n // 2} × {usd(a + last)} = {usd(total)}.")
        else:
            avg = (a + last) // 2
            steps.append(f"With {n} weeks, the average week is {usd(a + last)} ÷ 2 = {usd(avg)}, so the total is "
                         f"{n} × {usd(avg)} = {usd(total)}.")
        ask = f"How much will {who} have set aside in all after {n} weeks?" if p['ci'] else \
            f"How much will {w} have saved in all after {n} weeks?"
        return dict(stem=stem, ask=ask, steps=steps)


@template(id='t5.lineup-together-apart.v1', tier=5, topic='counting', kind='int', unit='orders', seconds=120)
class LineupTogetherApart:
    @staticmethod
    def params(r):
        var = r.pick(['together', 'apart', 'trio'])
        n = r.int(4, 6) if var != 'trio' else r.int(5, 6)
        skin = r.pick(['photo', 'movie'])
        names = r.people(3 if var == 'trio' else 2)
        x = r.pick([40, 50, 60, 75]) if skin == 'photo' else r.pick([95, 105, 110, 120])
        return dict(var=var, n=n, skin=skin, names=names, x=x)

    fallback = dict(var='together', n=5, skin='photo', names=[person('Luis'), person('Priya')], x=50)

    @staticmethod
    def solve(p):
        n, var = p['n'], p['var']
        count = 0
        for perm in itertools.permutations(range(n)):
            pos = {v: i for i, v in enumerate(perm)}
            if var == 'together':
                ok = abs(pos[0] - pos[1]) == 1
            elif var == 'apart':
                ok = abs(pos[0] - pos[1]) != 1
            else:
                ok = max(pos[0], pos[1], pos[2]) - min(pos[0], pos[1], pos[2]) == 2
            count += ok
        return count

    @staticmethod
    def render(p):
        n, var, nm = p['n'], p['var'], p['names']
        k = n - len(nm)
        if p['skin'] == 'photo':
            group = join_and([str(x) for x in nm] + [f"{word(k)} of their cousins"])
            intro = f"{group} are lining up in one row for a family photo."
            if var == 'together':
                rule = f"{nm[0]} and {nm[1]} are twins and insist on standing next to each other."
            elif var == 'apart':
                rule = f"{nm[0]} and {nm[1]} keep making each other laugh, so they can't stand side by side."
            else:
                rule = f"{nm[0]}, {nm[1]} and {nm[2]} are triplets and want to stand together, side by side."
            irr = f"The photographer charges {usd(p['x'] * 100)} for the session."
            ask = f"In how many different orders can the {n} of them line up?"
        else:
            intro = (f"{cap(word(n))} friends, including {join_and([str(x) for x in nm])}, have {n} seats together "
                     f"in one row at the movies.")
            if var == 'together':
                rule = f"{nm[0]} and {nm[1]} want to sit next to each other to share popcorn."
            elif var == 'apart':
                rule = f"{nm[0]} and {nm[1]} both talk during movies, so the group agrees they won't sit side by side."
            else:
                rule = f"{nm[0]}, {nm[1]} and {nm[2]} want three seats in a row together."
            irr = f"The movie runs {p['x']} minutes."
            ask = f"In how many different ways can the {n} friends fill the {n} seats?"
        stem = f"{intro} {rule} {irr}"
        if var == 'together':
            blk = fact(n - 1)
            steps = [f"Glue {nm[0]} and {nm[1]} into one block, leaving {n - 1} units to arrange.",
                     f"{n - 1} units can be ordered {chain(n - 1)} = {blk} ways.",
                     f"Inside the block they can switch places: {blk} × 2 = {blk * 2}."]
        elif var == 'apart':
            tot, tog = fact(n), 2 * fact(n - 1)
            steps = [f"With no rule: {chain(n)} = {tot} orders.",
                     f"Orders with them together: glue them into a block, {chain(n - 1)} = {fact(n - 1)}, "
                     f"times 2 for their order = {tog}.",
                     f"Not together: {tot} − {tog} = {tot - tog}."]
        else:
            blk = fact(n - 2)
            steps = [f"Glue the three into one block, leaving {n - 2} units: {chain(n - 2)} = {blk} orders.",
                     "Inside the block the three can be ordered 3 × 2 × 1 = 6 ways.",
                     f"Total: {blk} × 6 = {blk * 6}."]
        return dict(stem=stem, ask=ask, steps=steps, unit='ways' if p['skin'] == 'movie' else 'orders')


@template(id='t5.prize-wheel-average.v1', tier=5, topic='probability', kind='money', seconds=120)
class PrizeWheelAverage:
    @staticmethod
    def params(r):
        N = r.pick([8, 10, 12, 20])
        p1, p2 = r.pick([500, 1000, 2000]), r.pick([100, 200, 300])
        k1, k2 = r.int(1, 2), r.int(2, 5)
        if k1 + k2 > N - 2:
            raise Retry
        T = k1 * p1 + k2 * p2
        if T % N:
            raise Retry
        E = T // N
        if E % 5:
            raise Retry
        c = r.pick([200, 300, 500])
        if not 25 <= c - E <= c - 25:
            raise Retry
        return dict(skin=r.pick(['wheel', 'ducks']), who=r.person(), N=N, p1=p1, p2=p2, k1=k1, k2=k2, c=c,
                    x=r.int(3, 8))

    fallback = dict(skin='wheel', who=person('Imani'), N=10, p1=1000, p2=200, k1=1, k2=3, c=300, x=5)

    @staticmethod
    def solve(p):
        prizes = [p['p1']] * p['k1'] + [p['p2']] * p['k2'] + [0] * (p['N'] - p['k1'] - p['k2'])
        return p['c'] - F(sum(prizes), len(prizes))

    @staticmethod
    def render(p):
        w, N, c = p['who'], p['N'], p['c']
        rest = N - p['k1'] - p['k2']
        if p['skin'] == 'wheel':
            stem = (f"{w} runs a prize wheel at the school fair. The wheel has {N} equal sections, each equally "
                    f"likely to land on top, and a spin costs {usd(c)}. The table shows what the sections pay. "
                    f"The fair runs for {p['x']} hours.")
            col, unit1, play = 'Sections', 'section', 'spin'
        else:
            stem = (f"{w}'s booth at the town festival has {N} rubber ducks floating in a pool. A player pays "
                    f"{usd(c)}, picks one duck at random, and wins the prize marked underneath; the duck then goes "
                    f"back in. The table shows the prizes. The festival lasts {p['x']} hours.")
            col, unit1, play = 'Ducks', 'duck', 'game'
        table = dict(headers=['Prize', col], rows=[[usd(p['p1']), p['k1']], [usd(p['p2']), p['k2']],
                                                   ['Nothing', rest]])
        T = p['k1'] * p['p1'] + p['k2'] * p['p2']
        E = T // N
        steps = [f"If each {unit1} came up once, the prizes would total {p['k1']} × {usd(p['p1'])} + {p['k2']} × "
                 f"{usd(p['p2'])} = {usd(T)}.",
                 f"Average prize per {play}: {usd(T)} ÷ {N} = {usd(E)}.",
                 f"The booth keeps {usd(c)} − {usd(E)} = {usd(c - E)} per {play} on average."]
        thing = 'the prize wheel' if p['skin'] == 'wheel' else 'the booth'
        ask = f"On average, how much money does {thing} make per {play} after paying out prizes?"
        return dict(stem=stem, ask=ask, steps=steps, table=table)


@template(id='t5.shadow-similar-triangles.v1', tier=5, topic='geometry', kind='dec', unit='feet', seconds=110)
class ShadowSimilarTriangles:
    OBJECTS = [('oak tree', "The tree was planted about {x} years ago."),
               ('flagpole', "The flagpole was put up {x} years ago."),
               ('light pole', "The parking lot around it has {x} spaces.")]

    @staticmethod
    def params(r):
        var = r.pick(['separate', 'separate', 'tips'])
        obj = r.pick(ShadowSimilarTriangles.OBJECTS)
        x = r.int(12, 60)
        if var == 'separate':
            h = r.pick([3, 5, 6])
            s1, s2 = r.int(2, 10), r.int(8, 90)
            H = F(h * s2, s1)
            if (H * 2).denominator != 1 or not 15 <= H <= 90 or H == s2 or s1 == h:
                raise Retry
            if s2 % s1 and h * s2 > 400:
                raise Retry
            if x in (H, s2, s1):
                raise Retry
            return dict(var=var, who=r.person(), obj=obj, h=h, s1=s1, s2=s2, x=x)
        h = r.pick([5, 6])
        s, d = r.int(3, 10), r.int(6, 40)
        H = F(h * (d + s), s)
        if (H * 2).denominator != 1 or not 12 <= H <= 60 or s == h or x in (H, d, s, d + s):
            raise Retry
        return dict(var=var, who=r.person(), obj=obj, h=h, s=s, d=d, x=x)

    fallback = dict(var='separate', who=person('Kenji'), obj=OBJECTS[0], h=6, s1=4, s2=30, x=20)

    @staticmethod
    def solve(p):
        # slope of the sun's rays (rise over run) is the same for both objects
        if p['var'] == 'separate':
            slope = F(p['h'], p['s1'])
            return slope * p['s2']
        slope = F(p['h'], p['s'])
        return slope * (p['d'] + p['s'])

    @staticmethod
    def render(p):
        w, (obj, irr), h = p['who'], p['obj'], p['h']
        irr = irr.format(x=p['x'])
        if p['var'] == 'separate':
            s1, s2 = p['s1'], p['s2']
            H = F(h * s2, s1)
            if h == 3:
                ref = (f"On level ground, {w} holds a 3-foot yardstick straight up, and its shadow is "
                       f"{plural(s1, 'foot', 'feet')} long.")
                thing = 'yardstick'
            else:
                ref = (f"{w}, who is {h} feet tall, stands on level ground and notices that {w.his} shadow is "
                       f"{plural(s1, 'foot', 'feet')} long.")
                thing = w
            stem = f"{ref} At the same moment, the shadow of a nearby {obj} is {s2} feet long. {irr}"
            steps = [f"The sun hits both at the same angle, so height ÷ shadow is the same for the {obj} and "
                     f"{'the yardstick' if h == 3 else w}: {h} ÷ {s1}."]
            if s2 % s1 == 0:
                steps += [f"The {obj}'s shadow is {s2} ÷ {s1} = {s2 // s1} times as long as {thing if h != 3 else 'the yardstick'}'s.",
                          f"So the {obj} is {s2 // s1} × {h} = {num(H)} feet tall."]
            else:
                steps += [f"Height of the {obj} = {s2} × {h} ÷ {s1} = {s2 * h} ÷ {s1} = {num(H)} feet."]
            return dict(stem=stem, ask=f"How tall is the {obj}, in feet?", steps=steps)
        s, d = p['s'], p['d']
        D = d + s
        H = F(h * D, s)
        art = 'an' if obj[0] in 'aeiou' else 'a'
        stem = (f"{w}, who is {h} feet tall, stands on level ground in the shadow of {art} {obj}, {d} feet from its "
                f"base. {w.His} own shadow is {s} feet long and points the same way, and its tip lands exactly on "
                f"the tip of the {obj}'s shadow. {irr}")
        steps = [f"The {obj}'s shadow runs past {w} to the same tip: {d} + {s} = {D} feet long.",
                 f"Same sun angle, so height ÷ shadow matches: {h} ÷ {s} for {w}.",
                 f"Height of the {obj} = {D} × {h} ÷ {s} = {D * h} ÷ {s} = {num(H)} feet."]
        return dict(stem=stem, ask=f"How tall is the {obj}, in feet?", steps=steps)


@template(id='t5.toward-each-other.v1', tier=5, topic='rates', kind='int', unit='minutes', seconds=120)
class TowardEachOther:
    SKINS = {
        'bike': ((8, 16), "{a} and {b} live {D} miles apart along a straight bike trail, and they ride toward each "
                          "other to meet for lunch.", 'rides', "The trail has {x} benches along the way."),
        'walk': ((2, 4), "{a} and {b} start at opposite ends of a {D}-mile lakeside path and walk toward each "
                         "other.", 'walks', "The lake is about {x} feet deep in the middle."),
        'drive': ((40, 65), "{a} and {b} are {D} miles apart on the same highway and drive toward each other to "
                            "meet for dinner.", 'drives',
                  "{a}'s car holds {x} gallons of gas."),
    }

    @staticmethod
    def params(r):
        skin = r.pick(sorted(TowardEachOther.SKINS))
        (lo, hi) = TowardEachOther.SKINS[skin][0]
        step = 5 if skin == 'drive' else 1
        v1, v2 = r.pick(range(lo, hi + 1, step)), r.pick(range(lo, hi + 1, step))
        if v1 == v2:
            raise Retry
        V = v1 + v2
        a, b = r.people(2)
        x = r.int(11, 16) if skin == 'drive' else r.int(6, 20)
        if r.chance(0.5):
            t = r.int(10, 90)
            D = F(V * t, 60)
            if (D * 2).denominator != 1 or D < 1 or (skin == 'drive' and D.denominator != 1):
                raise Retry
            return dict(skin=skin, a=a, b=b, v1=v1, v2=v2, D=D, L=0, after='a', x=x)
        L = r.pick([5, 10, 15, 20, 30])
        d1 = F(v1 * L, 60)
        tau = r.int(6, 75)
        R = F(V * tau, 60)
        if (d1 * 2).denominator != 1 or (R * 2).denominator != 1 or R < 1 or \
                (skin == 'drive' and (d1 + R).denominator != 1):
            raise Retry
        return dict(skin=skin, a=a, b=b, v1=v1, v2=v2, D=d1 + R, L=L, after=r.pick(['a', 'b']), x=x)

    fallback = dict(skin='bike', a=person('Felix'), b=person('Hana'), v1=12, v2=8, D=F(15), L=0, after='a', x=9)

    @staticmethod
    def solve(p):
        # walk the clock forward one minute at a time
        for t in range(0, 1000):
            pa = F(p['v1'] * t, 60)
            pb = F(p['v2'] * max(0, t - p['L']), 60)
            if pa + pb >= p['D']:
                assert pa + pb == p['D']
                return t if p['after'] == 'a' else t - p['L']
        raise ValueError

    @staticmethod
    def render(p):
        a, b, v1, v2, D, L = p['a'], p['b'], p['v1'], p['v2'], p['D'], p['L']
        _, intro, verb, irr = TowardEachOther.SKINS[p['skin']]
        V = v1 + v2
        speeds = f"{a} {verb} at {v1} miles per hour, and {b} {verb} at {v2} miles per hour."
        f = dict(a=a, b=b, D=num(D), x=p['x'])
        if L == 0:
            stem = f"{intro.format(**f)} {speeds} They leave at the same time. {irr.format(**f)}"
            t = F(D) / V
            steps = [f"The gap closes at {v1} + {v2} = {V} miles per hour.",
                     f"Time to close {plural(D, 'mile')}: {num(D)} ÷ {V} = {frac(t)} {'hour' if t <= 1 else 'hours'}.",
                     f"{frac(t)} × 60 = {num(t * 60)} minutes."]
            ask = "How many minutes after they leave do they meet?"
        else:
            stem = f"{intro.format(**f)} {speeds} {b} leaves {L} minutes after {a}. {irr.format(**f)}"
            d1 = F(v1 * L, 60)
            R = D - d1
            tau = R / V * 60
            steps = [f"Head start: in {L} minutes, {a} covers {v1} × {frac(F(L, 60))} = {plural(d1, 'mile')}.",
                     f"Distance left when {b} leaves: {num(D)} − {num(d1)} = {plural(R, 'mile')}.",
                     f"Together they close {v1} + {v2} = {V} miles per hour: {num(R)} ÷ {V} = {frac(R / V)} {'hour' if R / V <= 1 else 'hours'} "
                     f"= {num(tau)} minutes after {b} leaves."]
            if p['after'] == 'a':
                steps.append(f"Counting from when {a} leaves: {L} + {num(tau)} = {num(tau + L)} minutes.")
            ask = f"How many minutes after {a if p['after'] == 'a' else b} leaves do they meet?"
        return dict(stem=stem, ask=ask, steps=steps)


# =====================================================================================
# BONUS (tier 6, puzzle)
# =====================================================================================

@template(id='b.handshake-count.v1', tier=6, topic='puzzle', kind='int', unit='handshakes', seconds=80)
class HandshakeCount:
    # (forward stem, inverse stem, act unit, people word, inverse ask)
    SKINS = [
        ("There are {n} people at {w}'s birthday party, counting {w}. Before the cake comes out, everyone shakes "
         "hands with everyone else exactly once.",
         "At {w}'s birthday party, every person there, {w} included, shook hands with every other person exactly "
         "once. {w} kept track and counted {H} handshakes in all.", 'handshakes', 'people',
         "How many people were at the party, counting {w}?"),
        ("Before a chess tournament, each of the {n} players shakes hands with every other player once. {w}, the "
         "organizer, just watches.",
         "Before a chess tournament, each player shook hands with every other player once. {w}, the organizer, "
         "counted {H} handshakes.", 'handshakes', 'players', "How many players are in the tournament?"),
        ("At a team dinner, {w} raises a glass, and each of the {n} people at the table clinks glasses with every "
         "other person exactly once.",
         "At a team dinner, each person at the table clinked glasses with every other person exactly once. {w} "
         "counted {H} clinks.", 'clinks', 'people', "How many people are at the table?"),
    ]

    @staticmethod
    def params(r):
        n = r.int(8, 30)
        return dict(who=r.person(), si=r.int(0, 2), n=n, inv=r.chance(0.45))

    fallback = dict(who=person('Leah'), si=0, n=12, inv=False)

    @staticmethod
    def solve(p):
        n = p['n']
        H = sum(1 for i in range(n) for j in range(n) if i < j)
        if not p['inv']:
            return H
        for m in range(2, 100):
            if sum(1 for i in range(m) for j in range(m) if i < j) == H:
                return m

    @staticmethod
    def render(p):
        w, n = p['who'], p['n']
        fwd, inv, act, folks, inv_ask = HandshakeCount.SKINS[p['si']]
        H = n * (n - 1) // 2
        if not p['inv']:
            stem = fwd.format(w=w, n=n)
            ask = f"How many {act} are there in all?"
            steps = [f"Each of the {n} {folks} takes part in {n - 1} {act}: {n} × {n - 1} = {n * (n - 1)}.",
                     f"That counts every one twice (once for each person in it), so divide by 2: "
                     f"{n * (n - 1)} ÷ 2 = {H}."]
            return dict(stem=stem, ask=ask, steps=steps, unit=act)
        stem = inv.format(w=w, H=H)
        steps = [f"With n {folks}, the count is n × (n − 1) ÷ 2, so n × (n − 1) ÷ 2 = {H}.",
                 f"Double it: n × (n − 1) = {2 * H}.",
                 f"Look for two numbers in a row that multiply to {2 * H}: {n} × {n - 1} = {2 * H}, so n = {n}."]
        return dict(stem=stem, ask=inv_ask.format(w=w), steps=steps, unit=folks)


@template(id='b.cuts-and-posts.v1', tier=6, topic='puzzle', kind='int', unit='minutes', seconds=70)
class CutsAndPosts:
    CUTS = [("It takes {w} {t} minutes to saw a log into {k} pieces for the fire pit. Each cut takes the same "
             "amount of time.", "At the same pace, how many minutes would it take {w} to saw an identical log into "
             "{m} pieces?", 'minutes'),
            ("{w} cuts a long board into {k} shelves in {t} minutes, making one straight cut at a time, and every "
             "cut takes the same time.", "At the same pace, how many minutes would it take to cut an identical board "
             "into {m} shelves?", 'minutes'),
            ("At a party, {w} slices a 6-foot sandwich into {k} pieces in {t} seconds, making every cut straight "
             "across at a steady pace.", "At that pace, how many seconds would it take to slice an identical "
             "sandwich into {m} pieces?", 'seconds')]

    @staticmethod
    def params(r):
        if r.chance(0.55):
            k, m = r.int(3, 6), r.int(7, 15)
            per = r.int(2, 9) if r.int(0, 2) < 2 else r.int(3, 12)
            ci = r.int(0, 2)
            if ci == 2:
                per = r.pick([2, 3, 4, 5])
            return dict(var='cut', who=r.person(), ci=ci, k=k, m=m, t=per * (k - 1))
        s = r.pick([4, 5, 6, 8, 10, 12])
        g = r.int(6, 25)
        return dict(var='posts', who=r.person(), s=s, L=s * g, both=r.chance(0.4))

    fallback = dict(var='cut', who=person('Ezra'), ci=0, k=4, m=10, t=12)

    @staticmethod
    def solve(p):
        if p['var'] == 'cut':
            # simulate: count cuts needed to reach a number of pieces
            def cuts(n):
                pieces, c = 1, 0
                while pieces < n:
                    pieces, c = pieces + 1, c + 1
                return c
            per = F(p['t'], cuts(p['k']))
            return per * cuts(p['m'])
        posts = len(range(0, p['L'] + 1, p['s']))
        return posts * (2 if p['both'] else 1)

    @staticmethod
    def render(p):
        w = p['who']
        if p['var'] == 'cut':
            txt, ask, unit = CutsAndPosts.CUTS[p['ci']]
            k, m, t = p['k'], p['m'], p['t']
            per = t // (k - 1)
            f = dict(w=w, k=k, m=m, t=t)
            steps = [f"{k} pieces take only {k - 1} cuts, so each cut takes {t} ÷ {k - 1} = {per} {unit}.",
                     f"{m} pieces take {m - 1} cuts: {m - 1} × {per} = {(m - 1) * per} {unit}."]
            return dict(stem=txt.format(**f), ask=ask.format(**f), steps=steps, unit=unit)
        s, L = p['s'], p['L']
        g = L // s
        if not p['both']:
            stem = (f"{w} is building a straight fence {L} feet long along the edge of {w.his} yard. {w.He} sets a "
                    f"post every {s} feet, with a post at each end.")
            ask = f"How many posts does {w} need?"
            unit = 'posts'
        else:
            stem = (f"The town is planting trees along both sides of a straight path that is {L} feet long. On each "
                    f"side, there will be a tree every {s} feet, with a tree at both ends. {w} volunteers to dig the "
                    f"holes.")
            ask = "How many trees will be planted in all?"
            unit = 'trees'
        steps = [f"{L} ÷ {s} = {g} equal gaps.",
                 f"There is one more {unit[:-1]} than gaps (count the end): {g} + 1 = {g + 1}."]
        if p['both']:
            steps.append(f"Both sides of the path: 2 × {g + 1} = {2 * (g + 1)} trees.")
        return dict(stem=stem, ask=ask, steps=steps, unit=unit)


@template(id='b.clock-strike-gaps.v1', tier=6, topic='puzzle', kind='int', unit='seconds', seconds=70)
class ClockStrikeGaps:
    SKINS = [("{w}'s grandfather clock strikes once for each hour, with the strikes evenly spaced. At {a} "
              "o'clock, it takes {X} seconds from the first strike to the last.", 'strike', 'strikes'),
             ("The bell in the town hall tower rings once for each hour, with the rings evenly spaced. {w} times it "
              "at {a} o'clock: {X} seconds pass from the first ring to the last.", 'ring', 'rings')]

    @staticmethod
    def params(r):
        a = r.int(3, 7)
        b = r.int(a + 3, 12)
        g = r.int(1, 4)
        return dict(who=r.person(), si=r.int(0, 1), a=a, b=b, g=g)

    fallback = dict(who=person('Ruth'), si=0, a=6, b=12, g=2)

    @staticmethod
    def solve(p):
        g = F(p['g'] * (p['a'] - 1), p['a'] - 1)
        hits = [i * g for i in range(p['b'])]
        return hits[-1] - hits[0]

    @staticmethod
    def render(p):
        w, a, b, g = p['who'], p['a'], p['b'], p['g']
        txt, one, many = ClockStrikeGaps.SKINS[p['si']]
        X = g * (a - 1)
        stem = txt.format(w=w, a=a, X=X)
        ask = f"How many seconds does it take from the first {one} to the last at {b} o'clock?"
        steps = [f"{a} {many} have only {a - 1} gaps between them, so each gap is {X} ÷ {a - 1} = "
                 f"{plural(g, 'second')}.",
                 f"{b} {many} have {b - 1} gaps: {b - 1} × {g} = {(b - 1) * g} seconds."]
        return dict(stem=stem, ask=ask, steps=steps)


@template(id='b.climb-and-slip.v1', tier=6, topic='puzzle', kind='int', unit=None, seconds=90)
class ClimbAndSlip:
    SKINS = [("A snail at the bottom of {aH}-foot well climbs {u} feet up the wall every day, then slides back "
              "{d} {dft} every night while it rests.", 'snail', 'the top of the well'),
             ("A frog at the bottom of {aH}-foot ditch hops {u} feet up the muddy bank every day, then slips back "
              "{d} {dft} every night.", 'frog', 'the top of the bank'),
             ("A beetle starts at the bottom of {aH}-foot garden wall. Every day it crawls {u} feet up, and every "
              "night it slides back down {d} {dft}. {w} checks on it each morning.", 'beetle', 'the top of the wall')]

    @staticmethod
    def params(r):
        u = r.int(3, 7)
        d = r.int(1, u - 1)
        k = r.int(3, 15)
        H = u + k * (u - d)
        if H > 60:
            raise Retry
        return dict(who=r.person(), si=r.int(0, 2), u=u, d=d, H=H)

    fallback = dict(who=person('Owen'), si=0, u=3, d=2, H=20)

    @staticmethod
    def solve(p):
        pos, day = 0, 0
        while True:
            day += 1
            pos += p['u']
            if pos >= p['H']:
                return day
            pos -= p['d']

    @staticmethod
    def render(p):
        u, d, H = p['u'], p['d'], p['H']
        txt, crit, top = ClimbAndSlip.SKINS[p['si']]
        stem = txt.format(w=p['who'], aH=a_an(H), u=u, d=d, dft='foot' if d == 1 else 'feet')
        net = u - d
        k = (H - u) // net
        ask = f"On which day does the {crit} first reach {top}, if the first day of climbing is day 1?"
        steps = [f"Each full day and night, the {crit} gains {u} − {d} = {plural(net, 'foot', 'feet')}.",
                 f"On its last day it climbs {u} feet and never slides back, so it only needs to start that day at "
                 f"{H} − {u} = {H - u} feet.",
                 f"Reaching {H - u} feet takes {H - u} ÷ {net} = {k} full days and nights.",
                 f"It reaches the top on day {k} + 1 = {k + 1}."]
        return dict(stem=stem, ask=ask, steps=steps)


@template(id='b.toggle-lockers.v1', tier=6, topic='puzzle', kind='int', unit='lockers', seconds=120)
class ToggleLockers:
    @staticmethod
    def params(r):
        n = r.int(30, 200)
        k = int(n ** 0.5)
        while (k + 1) * (k + 1) <= n:
            k += 1
        while k * k > n:
            k -= 1
        ask_on = r.chance(0.65)
        ans = k if ask_on else n - k
        if str(ans) in str(n):
            raise Retry
        return dict(who=r.person(), skin=r.pick(['lockers', 'lamps']), n=n, ask_on=ask_on)

    fallback = dict(who=person('Caleb'), skin='lockers', n=150, ask_on=True)

    @staticmethod
    def solve(p):
        state = [False] * (p['n'] + 1)
        for s in range(1, p['n'] + 1):
            for i in range(s, p['n'] + 1, s):
                state[i] = not state[i]
        on = sum(state[1:])
        return on if p['ask_on'] else p['n'] - on

    @staticmethod
    def render(p):
        n, w = p['n'], p['who']
        if p['skin'] == 'lockers':
            stem = (f"A hallway at {w}'s school has {n} closed lockers, numbered 1 to {n}. Then {n} students walk "
                    f"by one at a time. Student 1 opens every locker. Student 2 switches every 2nd locker (closing it "
                    f"if open, opening it if closed), student 3 switches every 3rd locker, and so on, until student "
                    f"{n} switches only locker {n}.")
            thing, things, on, off = 'locker', 'lockers', 'open', 'closed'
        else:
            stem = (f"A hotel hallway has {n} lamps, numbered 1 to {n}, all switched off. One by one, {n} guests walk "
                    f"past. Guest 1 flips the switch on every lamp, guest 2 flips every 2nd lamp, guest 3 flips every "
                    f"3rd lamp, and so on, until guest {n} flips only lamp {n}. {w} is the last guest.")
            thing, things, on, off = 'lamp', 'lamps', 'on', 'off'
        k = 0
        while (k + 1) ** 2 <= n:
            k += 1
        squares = ', '.join(str(i * i) for i in range(1, 4)) + f", …, {k * k}"
        steps = [f"A {thing} is switched once for each number that divides it (lamp 12: by 1, 2, 3, 4, 6, 12)."
                 if thing == 'lamp' else
                 f"A {thing} is switched once for each number that divides it (locker 12: by 1, 2, 3, 4, 6, 12).",
                 f"Divisors come in pairs (1 × 12, 2 × 6, 3 × 4), so most {things} are switched an even number of "
                 f"times and end {off}.",
                 f"Only perfect squares have an odd number of divisors, because one pair repeats (6 × 6 = 36).",
                 f"Perfect squares up to {n}: {squares}, which is {k} {things} {on}."]
        if not p['ask_on']:
            steps.append(f"{cap(off)}: {n} − {k} = {n - k} {things}.")
        ask = f"How many {things} are {on if p['ask_on'] else off} at the end?"
        return dict(stem=stem, ask=ask, steps=steps, unit=things)


@template(id='b.rows-gauss-sum.v1', tier=6, topic='puzzle', kind='int', unit='seats', seconds=90)
class RowsGaussSum:
    @staticmethod
    def params(r):
        if r.chance(0.6):
            R, a, d = r.int(10, 30), r.int(10, 30), r.pick([2, 2, 3, 4])
            total = R * (2 * a + (R - 1) * d) // 2
            if total > 3000:
                raise Retry
            return dict(var='seats', who=r.person(), R=R, a=a, d=d, place=r.pick(['amphitheater', 'theater',
                                                                                  'stadium section']))
        b, t = r.int(12, 30), r.int(1, 5)
        return dict(var='cans', who=r.person(), b=b, t=t)

    fallback = dict(var='seats', who=person('Isaac'), R=20, a=12, d=2, place='amphitheater')

    @staticmethod
    def solve(p):
        if p['var'] == 'seats':
            return sum(p['a'] + i * p['d'] for i in range(p['R']))
        return sum(range(p['t'], p['b'] + 1))

    @staticmethod
    def render(p):
        w = p['who']
        if p['var'] == 'seats':
            R, a, d = p['R'], p['a'], p['d']
            L = a + (R - 1) * d
            stem = (f"{w} is helping sell tickets for an outdoor {p['place']} with {R} rows of seats. The front row "
                    f"has {a} seats, and each row behind it has {d} more seats than the row in front of it.")
            ask = "How many seats are there in all?"
            steps = [f"Back row: {a} + {R - 1} × {d} = {L} seats."]
            unit, first, last, many = 'seats', a, L, R
        else:
            b, t = p['b'], p['t']
            rows = b - t + 1
            stem = (f"{w} is stacking soup cans into a flat, triangle-shaped display in a store window. The bottom row "
                    f"has {b} cans, each row has one fewer can than the row below it, and the top row has "
                    f"{plural(t, 'can')}.")
            ask = "How many cans are in the display?"
            steps = [f"Rows: from {t} up to {b} cans is {b} − {t} + 1 = {rows} rows."]
            unit, first, last, many = 'cans', t, b, rows
        tot = many * (first + last) // 2
        steps.append(f"Pair the first and last rows, the second and second-to-last, and so on: each pair holds "
                     f"{first} + {last} = {first + last}.")
        if many % 2 == 0:
            steps.append(f"{many} rows make {many // 2} pairs: {many // 2} × {first + last} = {num(tot)} {unit}.")
        else:
            avg = (first + last) // 2
            steps.append(f"With {many} rows, the average row is {first + last} ÷ 2 = {avg}, so the total is "
                         f"{many} × {avg} = {num(tot)} {unit}.")
        return dict(stem=stem, ask=ask, steps=steps, unit=unit)


@template(id='b.grab-in-the-dark.v1', tier=6, topic='puzzle', kind='int', unit='socks', seconds=90)
class GrabInTheDark:
    COLORS = ['black', 'white', 'gray', 'blue']

    @staticmethod
    def params(r):
        var = r.pick(['target', 'three', 'gloves'])
        w = r.person()
        if var == 'target':
            counts = [r.int(3, 12) for _ in range(3)]
            ti = r.int(0, 2)
            ans = sum(counts) - counts[ti] + 2
            if ans in counts or len(set(counts)) < 3:
                raise Retry
            return dict(var=var, who=w, counts=counts, ti=ti, skin=r.pick(['socks', 'pencils']))
        if var == 'three':
            c = r.int(3, 4)
            counts = [r.int(6, 20) for _ in range(c)]
            if 2 * c + 1 in counts or len(set(counts)) < c:
                raise Retry
            return dict(var=var, who=w, counts=counts)
        p1, p2 = r.int(3, 6), r.int(3, 6)
        if p1 + p2 + 1 in (p1, p2):
            raise Retry
        return dict(var=var, who=w, counts=[p1, p2])

    fallback = dict(var='target', who=person('Amara'), counts=[6, 4, 9], ti=1, skin='socks')

    @staticmethod
    def solve(p):
        # brute force: the largest handful that still fails, plus one
        counts, var = p['counts'], p['var']
        if var == 'target':
            caps = [min(n, 2) if i == p['ti'] else n for i, n in enumerate(counts)]
            best = max(sum(x) for x in itertools.product(*[range(c + 1) for c in caps]) if x[p['ti']] < 2)
            return best + 1
        if var == 'three':
            caps = [min(n, 3) for n in counts]
            best = max(sum(x) for x in itertools.product(*[range(c + 1) for c in caps]) if max(x) < 3)
            return best + 1
        p1, p2 = counts
        best = 0
        for bl, br, nl, nr in itertools.product(range(p1 + 1), range(p1 + 1), range(p2 + 1), range(p2 + 1)):
            if not (bl and br) and not (nl and nr):
                best = max(best, bl + br + nl + nr)
        return best + 1

    @staticmethod
    def render(p):
        w, counts, var = p['who'], p['counts'], p['var']
        if var == 'target':
            noun = 'socks' if p['skin'] == 'socks' else 'pencils'
            cols = ['black', 'white', 'gray'] if noun == 'socks' else ['red', 'blue', 'green']
            tgt = cols[p['ti']]
            listing = join_and([f"{n} {c}" for n, c in zip(counts, cols)])
            if noun == 'socks':
                stem = (f"During a power outage, {w} reaches into {w.his} sock drawer in total darkness. The drawer "
                        f"holds {listing} socks, all loose and all the same size.")
            else:
                stem = (f"{w} is blindfolded for a party game and reaches into a box of {listing} colored pencils, "
                        f"which all feel the same.")
            ask = f"What is the fewest {noun} {w} must pull out to be sure of getting two {tgt} {noun}?"
            others = [n for i, n in enumerate(counts) if i != p['ti']]
            O = sum(others)
            steps = [f"Worst case: {w.he} pulls every non-{tgt} one first: {others[0]} + {others[1]} = {O}.",
                     f"Even the next one only gives {w.him} a single {tgt} one.",
                     f"One more must be {tgt}, making two: {O} + 2 = {O + 2} {noun}."]
            return dict(stem=stem, ask=ask, steps=steps, unit=noun)
        if var == 'three':
            c = len(counts)
            cols = ['red', 'green', 'yellow', 'blue'][:c]
            listing = join_and([f"{n} {col}" for n, col in zip(counts, cols)])
            stem = (f"A gumball machine holds {listing} gumballs, well mixed. Each coin gives one gumball at random. "
                    f"{w} wants three gumballs of the same color for a craft project.")
            ask = f"What is the fewest gumballs {w} must get to be sure of having three of the same color?"
            steps = [f"Worst case: {w.he} gets two of every color and no third: 2 × {c} = {2 * c} gumballs.",
                     f"The next gumball must be a third of some color: {2 * c} + 1 = {2 * c + 1} gumballs."]
            return dict(stem=stem, ask=ask, steps=steps, unit='gumballs')
        p1, p2 = counts
        stem = (f"{w}'s mudroom bin holds {plural(p1, 'pair')} of black gloves and {plural(p2, 'pair')} of brown "
                f"gloves, all jumbled together. Each glove fits only a left hand or only a right hand. It's still "
                f"dark when {w} heads out, so {w.he} grabs gloves without looking.")
        ask = f"What is the fewest gloves {w} must grab to be sure of getting a left and a right glove of the same color?"
        steps = [f"Worst case: every glove {w.he} grabs is a left glove: {p1} + {p2} = {p1 + p2} gloves, and still "
                 f"no match.",
                 f"Now only right gloves are left, so the next one matches a left glove of its color: "
                 f"{p1 + p2} + 1 = {p1 + p2 + 1} gloves."]
        return dict(stem=stem, ask=ask, steps=steps, unit='gloves')


@template(id='b.stairs-one-or-two.v1', tier=6, topic='puzzle', kind='int', unit='ways', seconds=120)
class StairsOneOrTwo:
    @staticmethod
    def params(r):
        three = r.chance(0.3)
        n = r.int(5, 9) if three else r.int(5, 12)
        return dict(who=r.person(), three=three, n=n, skin=r.pick(['stairs', 'stones', 'porch']))

    fallback = dict(who=person('Zoe'), three=False, n=8, skin='stairs')

    @staticmethod
    def solve(p):
        moves = (1, 2, 3) if p['three'] else (1, 2)
        count = 0
        stack = [0]
        while stack:  # enumerate every sequence of moves explicitly
            pos = stack.pop()
            if pos == p['n']:
                count += 1
                continue
            for m in moves:
                if pos + m <= p['n']:
                    stack.append(pos + m)
        return count

    @staticmethod
    def render(p):
        w, n, three = p['who'], p['n'], p['three']
        moves = 'one, two or three' if three else 'one or two'
        if p['skin'] == 'stairs':
            stem = (f"The staircase up to {w}'s apartment has {n} steps. {w.He} climbs either {moves} steps at a "
                    f"time, mixing them however {w.he} likes.")
            ask = f"In how many different ways can {w} climb the {n} steps?"
            spot = 'step'
        elif p['skin'] == 'porch':
            stem = (f"{w}'s little cousin is racing up a set of {n} porch steps. Each jump takes {w.his} cousin up "
                    f"{moves} steps, in any mix, and the last jump has to land exactly on the top step.")
            ask = f"How many different ways can the climb up all {n} steps go?"
            spot = 'step'
        else:
            stem = (f"A row of {n} stepping stones crosses a creek. {w} starts on the bank, and each hop moves "
                    f"{w.him} forward {moves} stones. {w.He} must end exactly on the last stone.")
            ask = f"In how many different ways can {w} hop from the bank to the last stone?"
            spot = 'stone'
        if three:
            seq = [1, 2, 4]
            while len(seq) < n:
                seq.append(seq[-1] + seq[-2] + seq[-3])
            steps = [f"To land on {spot} k, the last move came from k − 1, k − 2 or k − 3, so ways(k) is the sum of "
                     f"the three before it.",
                     f"{cap(spot)} 1: 1 way. {cap(spot)} 2: 2 ways. {cap(spot)} 3: 4 ways.",
                     f"Keep adding three at a time: {', '.join(map(str, seq))}. So {spot} {n} has {seq[-1]} ways."]
        else:
            seq = [1, 2]
            while len(seq) < n:
                seq.append(seq[-1] + seq[-2])
            steps = [f"To land on {spot} k, the last move came from k − 1 or k − 2, so ways(k) = ways(k − 1) + "
                     f"ways(k − 2).",
                     f"{cap(spot)} 1: 1 way. {cap(spot)} 2: 2 ways (1 + 1 or 2).",
                     f"Keep adding: {', '.join(map(str, seq))}. So {spot} {n} has {seq[-1]} ways."]
        return dict(stem=stem, ask=ask, steps=steps)


@template(id='b.weekday-count-ahead.v1', tier=6, topic='puzzle', kind='int', unit='classes', seconds=80)
class WeekdayCountAhead:
    @staticmethod
    def params(r):
        today, tgt = r.sample(range(7), 2)
        N = r.int(30, 100)
        if N % 7 == 0:
            raise Retry
        return dict(who=r.person(), skin=r.pick(['gym', 'trash', 'camp']), today=today, tgt=tgt, N=N)

    fallback = dict(who=person('Victor'), skin='gym', today=2, tgt=5, N=45)

    @staticmethod
    def solve(p):
        return sum(1 for i in range(1, p['N'] + 1) if (p['today'] + i) % 7 == p['tgt'])

    @staticmethod
    def render(p):
        w, N = p['who'], p['N']
        today, tgt = DAYS[p['today']], DAYS[p['tgt']]
        if p['skin'] == 'gym':
            stem = (f"Today is {today}. {w}'s new gym pass starts tomorrow and is good for {N} days in a row. "
                    f"{w.His} favorite spin class meets once a week, every {tgt}.")
            ask = f"How many {tgt} spin classes fall within the {N} days of {w.his} pass?"
            unit = 'classes'
        elif p['skin'] == 'trash':
            stem = (f"Today is {today}. {w} will be away for the next {N} days, starting tomorrow. Trash is picked up "
                    f"every {tgt} morning, so {w.his} neighbor has offered to take the bins out while {w.he} is gone.")
            ask = f"How many {tgt} pickups will fall during those {N} days?"
            unit = 'pickups'
        else:
            stem = (f"Today is {today}. A summer art program that {w} signed up for starts tomorrow and meets every "
                    f"day for {N} days in a row. Every {tgt} is pizza day.")
            ask = f"How many pizza days will the program have?"
            unit = 'pizza days'
        q, rem = divmod(N, 7)
        extra = [DAYS[(p['today'] + i) % 7] for i in range(1, rem + 1)]
        hit = tgt in extra
        if rem == 1:
            span = (f"The 1 extra day falls on the same weekday as tomorrow, a {extra[0]}, so it "
                    f"{'adds one more' if hit else 'adds no'} {tgt}.")
        else:
            run = f"{extra[0]} and {extra[1]}" if rem == 2 else f"{extra[0]} through {extra[-1]}"
            span = (f"The {rem} extra days fall on the same weekdays as the first {rem}: {run}, which "
                    f"{'includes one more' if hit else 'does not include a'} {tgt}.")
        steps = [f"{N} days = {q} full weeks ({q} × 7 = {7 * q}) + {plural(rem, 'extra day')}.",
                 f"Each full week has exactly one {tgt}: {q}.",
                 span,
                 f"Total: {q} + {int(hit)} = {q + int(hit)}."]
        return dict(stem=stem, ask=ask, steps=steps, unit=unit)


@template(id='b.page-number-digits.v1', tier=6, topic='puzzle', kind='int', unit='digits', seconds=100)
class PageNumberDigits:
    @staticmethod
    def params(r):
        inv = r.chance(0.4)
        n = r.int(120, 400) if inv else r.int(60, 400)
        return dict(who=r.person(), inv=inv, n=n, skin=r.pick(['scrapbook', 'report', 'mailboxes']))

    fallback = dict(who=person('Tess'), inv=False, n=150, skin='scrapbook')

    @staticmethod
    def solve(p):
        D = sum(len(str(i)) for i in range(1, p['n'] + 1))
        if not p['inv']:
            return D
        m, used = 0, 0
        while used < D:
            m += 1
            used += len(str(m))
        return m

    @staticmethod
    def render(p):
        w, n = p['who'], p['n']
        D = sum(len(str(i)) for i in range(1, n + 1))
        if p['skin'] == 'mailboxes':
            thing, things = 'mailbox', 'mailboxes'
            if p['inv']:
                stem = (f"{w} manages an apartment building whose mailboxes are numbered 1, 2, 3 and so on with no "
                        f"gaps. Each number is made of stick-on digits, one sticker per digit, and the building used "
                        f"{num(D)} digit stickers in all.")
            else:
                stem = (f"{w} manages an apartment building with {n} mailboxes, numbered 1 to {n}. {w.He} is "
                        f"replacing the labels with stick-on digits, one sticker per digit.")
        else:
            thing, things = 'page', 'pages'
            book = f"{w.his} scrapbook" if p['skin'] == 'scrapbook' else 'a long report'
            how = 'by hand with a number stamp' if p['skin'] == 'scrapbook' else 'one digit at a time'
            if p['inv']:
                stem = (f"{w} numbered every page of {book}, starting at 1, {how}. When {w.he} finished, {w.he} "
                        f"had printed {num(D)} digits in all.")
            else:
                stem = f"{w} is numbering the pages of {book}, from page 1 to page {n}, {how}."
        if not p['inv']:
            ask = (f"How many digit stickers does {w} need in all?" if p['skin'] == 'mailboxes'
                   else "How many digits will that take in all?")
            if n < 100:
                steps = [f"{cap(things)} 1–9: 9 × 1 = 9 digits.",
                         f"{cap(things)} 10–{n}: {n - 9} × 2 = {(n - 9) * 2} digits.",
                         f"Total: 9 + {(n - 9) * 2} = {D}."]
            else:
                steps = [f"{cap(things)} 1–9: 9 × 1 = 9 digits.",
                         f"{cap(things)} 10–99: 90 × 2 = 180 digits.",
                         f"{cap(things)} 100–{n}: {n - 99} × 3 = {(n - 99) * 3} digits.",
                         f"Total: 9 + 180 + {(n - 99) * 3} = {num(D)}."]
            return dict(stem=stem, ask=ask, steps=steps)
        ask = (f"How many mailboxes does the building have?" if p['skin'] == 'mailboxes'
               else f"How many pages does {'the scrapbook' if p['skin'] == 'scrapbook' else 'the report'} have?")
        rest = D - 189
        steps = [f"{cap(things)} 1–9 use 9 digits and {things} 10–99 use 90 × 2 = 180, so 189 digits through "
                 f"{thing} 99.",
                 f"Digits left: {num(D)} − 189 = {rest}. Each {thing} from 100 on uses 3: {rest} ÷ 3 = {rest // 3} "
                 f"{things}.",
                 f"Those are {things} 100 through {99 + rest // 3}, so there are {n} {things}."]
        return dict(stem=stem, ask=ask, steps=steps, unit=things)


@template(id='b.squares-in-grid.v1', tier=6, topic='puzzle', kind='int', unit='squares', seconds=110)
class SquaresInGrid:
    SKINS = [("{w} is laying a {dims} patio of square tiles, all the same size.", 'patio', 'single tiles'),
             ("{w} is sewing a quilt that is a {dims} grid of square patches.", 'quilt', 'single patches'),
             ("A window in {w}'s attic is divided into a {dims} grid of square panes.", 'window', 'single panes')]

    @staticmethod
    def params(r):
        if r.chance(0.6):
            m = n = r.int(3, 8)
        else:
            m, n = r.int(2, 5), r.int(3, 8)
            if n <= m:
                raise Retry
        return dict(who=r.person(), si=r.int(0, 2), m=m, n=n)

    fallback = dict(who=person('Hugo'), si=0, m=5, n=5)

    @staticmethod
    def solve(p):
        m, n = p['m'], p['n']
        count = 0
        for top in range(m):
            for left in range(n):
                for size in range(1, 9):
                    if top + size <= m and left + size <= n:
                        count += 1
        return count

    @staticmethod
    def render(p):
        w, m, n = p['who'], p['m'], p['n']
        txt, thing, singles = SquaresInGrid.SKINS[p['si']]
        dims = f"{m}-by-{n}"
        stem = (txt.format(w=w, dims=dims) + f" Looking at the grid lines, {w} wonders how many squares can be "
                f"traced, counting every size, from {singles} up to the biggest square that fits.")
        ask = f"How many squares of all sizes are in the {dims} grid?"
        parts = [(k, (m - k + 1) * (n - k + 1)) for k in range(1, min(m, n) + 1)]
        total = sum(c for _, c in parts)
        if m == n:
            s1 = f"A k-by-k square can start in {n} − k + 1 spots across and the same number down, so there are ({n} − k + 1)² of them."
        else:
            s1 = f"A k-by-k square can start in {n} − k + 1 spots across and {m} − k + 1 spots down."
        steps = [s1,
                 "By size: " + ', '.join(f"{k}-by-{k}: {c}" for k, c in parts) + ".",
                 f"Total: {' + '.join(str(c) for _, c in parts)} = {total}."]
        return dict(stem=stem, ask=ask, steps=steps)


@template(id='b.costs-more-than.v1', tier=6, topic='puzzle', kind='money', seconds=60)
class CostsMoreThan:
    # (pricier, cheaper, where, choices for the difference D, choices for the cheaper price x), in cents
    ITEMS = [('baseball bat', 'ball', 'at a sporting goods store', [1500, 2000, 2500], [350, 450, 650, 850]),
             ('notebook', 'pen', 'at the campus bookstore', [100, 200, 300], [25, 35, 45, 75, 95, 125]),
             ('sandwich', 'bottle of juice', 'at a deli', [300, 400, 500, 600], [75, 95, 125, 150, 175, 225]),
             ('dog bed', 'leash', 'at a pet store', [1500, 2000, 2500, 3000], [450, 650, 750, 850, 1150]),
             ('board game', 'deck of cards', 'at a toy shop', [1500, 2000, 2500], [225, 275, 350, 450])]

    @staticmethod
    def params(r):
        it = r.pick(CostsMoreThan.ITEMS)
        D, x = r.pick(it[3]), r.pick(it[4])
        return dict(who=r.person(), it=it, D=D, x=x, ask_cheap=r.chance(0.7))

    fallback = dict(who=person('Esme'), it=ITEMS[0], D=2000, x=450, ask_cheap=True)

    @staticmethod
    def solve(p):
        T = 2 * p['x'] + p['D']
        for c in range(T + 1):
            if c + (c + p['D']) == T:
                return c if p['ask_cheap'] else c + p['D']

    @staticmethod
    def render(p):
        w, (big, small, where, _, _), D, x = p['who'], p['it'], p['D'], p['x']
        T = 2 * x + D
        stem = (f"{w} buys a {big} and a {small} {where} for {usd(T)} in total. The {big} costs exactly {usd(D)} more "
                f"than the {small}.")
        ask = f"How much does the {small if p['ask_cheap'] else big} cost?"
        steps = [f"Call the price of the {small} x, so the {big} costs x + {usd(D)}.",
                 f"x + (x + {usd(D)}) = {usd(T)}, so 2x = {usd(T)} − {usd(D)} = {usd(T - D)}.",
                 f"x = {usd(T - D)} ÷ 2 = {usd(x)} for the {small}."]
        if not p['ask_cheap']:
            steps.append(f"The {big}: {usd(x)} + {usd(D)} = {usd(x + D)}.")
        return dict(stem=stem, ask=ask, steps=steps)
