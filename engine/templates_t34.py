"""Tier 3 (Two-step) and tier 4 (Tricky) templates for Back of the Envelope."""
from fractions import Fraction as F
from math import gcd, isqrt

from engine import Retry, template, person, usd, usd2, num, pct, frac, plural, word, cap, ordinal, a_an


def _fmt(s, w, **kw):
    """Fill a context string with a person's name and pronouns plus extra fields."""
    return s.format(w=w, he=w.he, He=w.He, him=w.him, his=w.his, His=w.His, **kw)


def _lcm(a, b):
    return a * b // gcd(a, b)


# =====================================================================================  TIER 3


@template(id='t3.percent-change.v1', tier=3, topic='percent', kind='pct', seconds=65)
class PercentChange:
    # (key, direction, old price range in dollars, allowed percents, irrelevant x choices, stem, ask)
    CONTEXTS = [
        ('bus', 'up', (30, 120), [10, 15, 20, 25, F(25, 2), 30, 40], list(range(16, 24)),
         "{w} buys a monthly bus pass. Last year the pass cost {old}, and this year the transit agency raised the "
         "price to {new}. {He} rides the bus about {x} days a month.",
         "By what percent did the price of the bus pass increase?"),
        ('internet', 'up', (40, 100), [5, 10, 15, 20, 25, F(25, 2), 30, 40], [200, 300, 500],
         "{w}'s home internet bill used to be {old} a month. After {he} upgraded {his} plan, the monthly bill "
         "became {new}. The new plan has a download speed of {x} megabits per second.",
         "By what percent did {w}'s monthly internet bill increase?"),
        ('bike', 'down', (160, 600), [10, 15, 20, 25, F(25, 2), 30, 35, 40, 50], list(range(3, 11)),
         "{w} has been watching a mountain bike at a sporting-goods store. It was priced at {old}, and this week "
         "the store marked it down to {new}. The sale ends in {x} days.",
         "By what percent was the price of the bike reduced?"),
        ('coffee', 'either', (8, 24), [5, 10, 15, 20, 25, F(25, 2), 30], list(range(9, 15)),
         "Last month, a bag of coffee beans at {w}'s grocery store cost {old}. This month the same bag costs "
         "{new}. {w} goes through about one bag every {x} days.",
         "By what percent did the price of the bag {dirword}?"),
    ]

    @staticmethod
    def params(r):
        ctx = r.pick(PercentChange.CONTEXTS)
        key, d, (lo, hi), pcts, xs = ctx[:5]
        up = d == 'up' or (d == 'either' and r.chance(0.5))
        p = F(r.pick(pcts))
        old = r.int(lo, hi)
        if (key == 'bike' and old % 10) or (key != 'coffee' and old % 5):
            raise Retry
        chg = old * p  # in cents, since old is in dollars
        if chg.denominator != 1 or chg % 50 or (key == 'bike' and chg % 100):
            raise Retry
        new = old * 100 + (chg if up else -chg)
        return dict(who=r.person(), key=key, old=old, new=int(new), up=up, x=r.pick(xs))

    fallback = dict(who=person('Dev'), key='bus', old=80, new=9200, up=True, x=20)

    @staticmethod
    def solve(p):
        return abs(F(p['new'], 100) - p['old']) / p['old'] * 100

    @staticmethod
    def render(p):
        ctx = next(c for c in PercentChange.CONTEXTS if c[0] == p['key'])
        w, old, new = p['who'], p['old'] * 100, p['new']
        stem = _fmt(ctx[5], w, old=usd(old), new=usd(new), x=num(p['x']))
        ask = _fmt(ctx[6], w, dirword='increase' if p['up'] else 'decrease')
        chg = abs(new - old)
        f = F(chg, old)
        steps = [
            f"Change in price: {usd(max(old, new))} − {usd(min(old, new))} = {usd(chg)}.",
            f"Compare it with the original price: {usd(chg)} ÷ {usd(old)} = {frac(f)} = {num(f)}.",
            f"As a percent, that is {'an increase' if p['up'] else 'a decrease'} of {pct(f * 100)}.",
        ]
        return dict(stem=stem, ask=ask, steps=steps)


@template(id='t3.original-price.v1', tier=3, topic='money', kind='money', seconds=75)
class OriginalPrice:
    # (item phrase, short name, store, price range in dollars, irrelevant sentence, x choices)
    CONTEXTS = [
        ('a pair of running shoes', 'shoes', 'a sporting-goods store', (50, 160),
         "Only {x} pairs in {his} size were left on the shelf.", [2, 3, 4, 5]),
        ('a desk lamp', 'lamp', 'a home-goods store', (30, 100),
         "The lamp came with {x} light bulbs in the box.", [2, 3]),
        ('a winter coat', 'coat', 'a department store', (80, 240),
         "The sale lasted {x} days.", [3, 4, 5, 6, 7]),
        ('a set of wireless headphones', 'headphones', 'an electronics store', (60, 200),
         "The headphones run about {x} hours on a full charge.", [20, 24, 30, 40]),
    ]

    @staticmethod
    def params(r):
        ci = r.int(0, len(OriginalPrice.CONTEXTS) - 1)
        lo, hi = OriginalPrice.CONTEXTS[ci][3]
        d = r.pick([10, 20, 25, 30, 40, 50])
        orig = r.int(lo, hi)
        if orig * (100 - d) % 100:
            raise Retry
        sale = orig * (100 - d) // 100
        c = r.pick([5, 10, 15, 20])
        if c * 3 > sale:
            raise Retry
        return dict(who=r.person(), ci=ci, d=d, c=c * 100, paid=(sale - c) * 100,
                    x=r.pick(OriginalPrice.CONTEXTS[ci][5]))

    fallback = dict(who=person('Rosa'), ci=0, d=20, c=1000, paid=7000, x=3)

    @staticmethod
    def solve(p):
        # original price o satisfies o * (1 - d/100) - c = paid
        return (F(p['paid'] + p['c']) / (1 - F(p['d'], 100)))

    @staticmethod
    def render(p):
        item, short, store, _, irr, _ = OriginalPrice.CONTEXTS[p['ci']]
        w, d, c, paid = p['who'], p['d'], p['c'], p['paid']
        sale = paid + c
        x = word(p['x']) if p['x'] <= 10 else num(p['x'])
        stem = (f"{w} bought {item} at {store} during a {d}%-off sale, and {w.he} also used a {usd(c)} coupon. "
                f"The register took {d}% off the original price first, then subtracted the coupon. "
                + _fmt(irr, w, x=x) + f" Before tax, {w} paid {usd(paid)}.")
        keep = F(100 - d, 100)
        steps = [
            f"Add the coupon back: {usd(paid)} + {usd(c)} = {usd(sale)}.",
            f"{usd(sale)} is what was left after {d}% off, so it is {100 - d}% of the original price.",
            f"Original price: {usd(sale)} ÷ {num(keep)} = {usd(int(sale / keep))}.",
        ]
        return dict(stem=stem, ask=f"What was the original price of the {short}?", steps=steps)


@template(id='t3.ratio-parts.v1', tier=3, topic='ratio', kind='int', unit='ounces', seconds=65)
class RatioParts:
    CONTEXTS = {
        'trail': dict(items=('peanuts', 'raisins', 'chocolate chips'), each='ounces', maxT=120,
                      stem="{w} is making trail mix for a weekend hike. {His} recipe mixes peanuts, raisins and "
                           "chocolate chips in the ratio {a}:{b}:{c} by weight. {He} wants {T} ounces of trail mix "
                           "in all, which {he}'ll pack into {x} bags.",
                      one="How many ounces of {i} should {w} use?",
                      more="How many more ounces of {i} than {j} will the mix contain?"),
        'bake': dict(items=('cookies', 'brownies', 'muffins'), each='items', maxT=180,
                     stem="{w}'s club ran a bake sale on Saturday morning. They sold cookies, brownies and muffins "
                          "in the ratio {a}:{b}:{c}, and they sold {T} items in all. Every item was priced at {x}.",
                     one="How many {i} did the club sell?",
                     more="How many more {i} than {j} did the club sell?"),
        'concrete': dict(items=('cement', 'sand', 'gravel'), each='buckets', maxT=72,
                         stem="{w} is mixing concrete for a garden path that is {x} feet long. {His} mix uses "
                              "cement, sand and gravel in the ratio {a}:{b}:{c} by volume. {He} needs {T} buckets "
                              "of mix in all.",
                         one="How many buckets of {i} does {w} need?",
                         more="How many more buckets of {i} than {j} does {w} need?"),
    }
    X = {'trail': [4, 5, 6, 8], 'bake': [150, 200, 250], 'concrete': [12, 15, 20, 24, 30]}

    @staticmethod
    def params(r):
        key = r.pick(sorted(RatioParts.CONTEXTS))
        ctx = RatioParts.CONTEXTS[key]
        ratio = [r.int(1, 6) for _ in range(3)]
        s = sum(ratio)
        if s not in (5, 6, 7, 8, 9, 10, 12) or gcd(gcd(ratio[0], ratio[1]), ratio[2]) != 1:
            raise Retry
        k = r.int(3, 15)
        T = s * k
        if T > ctx['maxT'] or T < 24:
            raise Retry
        if r.chance(0.5):
            ask = ('one', r.int(0, 2), None)
        else:
            i, j = r.sample(range(3), 2)
            if ratio[i] <= ratio[j]:
                i, j = j, i
            if ratio[i] == ratio[j]:
                raise Retry
            ask = ('more', i, j)
        return dict(who=r.person(), key=key, ratio=ratio, T=T, ask=ask, x=r.pick(RatioParts.X[key]))

    fallback = dict(who=person('Maya'), key='trail', ratio=[3, 2, 1], T=48, ask=('one', 1, None), x=6)

    @staticmethod
    def solve(p):
        a = p['ratio']
        kind, i, j = p['ask']
        share = F(p['T'], sum(a))
        return share * a[i] if kind == 'one' else share * (a[i] - a[j])

    @staticmethod
    def render(p):
        ctx = RatioParts.CONTEXTS[p['key']]
        w, (a, b, c), T = p['who'], p['ratio'], p['T']
        items = ctx['items']
        kind, i, j = p['ask']
        x = usd(p['x']) if p['key'] == 'bake' else word(p['x']) if p['key'] == 'trail' else num(p['x'])
        stem = _fmt(ctx['stem'], w, a=a, b=b, c=c, T=T, x=x)
        s = a + b + c
        k = T // s
        unit = ctx['each']
        if p['key'] == 'bake':
            unit_ans = items[i]
        else:
            unit_ans = unit
        steps = [f"Total parts: {a} + {b} + {c} = {s}.",
                 f"Each part is {T} ÷ {s} = {k} {unit}."]
        if kind == 'one':
            ask = _fmt(ctx['one'], w, i=items[i])
            steps.append(f"{cap(items[i])}: {p['ratio'][i]} parts × {k} = {num(p['ratio'][i] * k)} {unit_ans}.")
        else:
            ask = _fmt(ctx['more'], w, i=items[i], j=items[j])
            d = p['ratio'][i] - p['ratio'][j]
            steps.append(f"{cap(items[i])} minus {items[j]}: {p['ratio'][i]} − {p['ratio'][j]} = "
                         f"{plural(d, 'part')}, and {d} × {k} = {num(d * k)} {unit_ans}.")
        return dict(stem=stem, ask=ask, steps=steps, unit=unit_ans)


@template(id='t3.ticket-mix.v1', tier=3, topic='algebra', kind='int', unit='tickets', seconds=85)
class TicketMix:
    # hi/lo: (singular, plural); lo price range; stem; ask per type
    CONTEXTS = {
        'play': dict(hi=('adult ticket', 'adult tickets'), lo=('student ticket', 'student tickets'), lp=(4, 8),
                     stem="{w} ran the ticket table for the drama club's spring play and sold {n} tickets in all. "
                          "Adult tickets cost {hp} and student tickets cost {lp}. The auditorium has {x} seats, and "
                          "at the end of the night the cash box held {R} from ticket sales.",
                     ask="How many {t} did {w} sell?", X=[300, 350, 400, 450]),
        'wash': dict(hi=('truck or SUV', 'trucks and SUVs'), lo=('car', 'cars'), lp=(6, 10),
                     stem="{w}'s swim team held a car wash to raise money. They charged {lp} for each car and {hp} "
                          "for each truck or SUV. Over {x} hours on Saturday, they washed {n} vehicles and "
                          "collected {R}.",
                     ask="How many {t} did the team wash?", X=[4, 5, 6]),
        'pancake': dict(hi=('adult plate', 'adult plates'), lo=("kids' plate", "kids' plates"), lp=(3, 7),
                        stem="{w} helped run a pancake breakfast at the fire station. Adult plates cost {hp} and "
                             "kids' plates cost {lp}. They served {n} plates and took in {R}, with {x} volunteers "
                             "working the griddles.",
                        ask="How many {t} did they serve?", X=[6, 8, 9, 12]),
    }

    @staticmethod
    def params(r):
        key = r.pick(sorted(TicketMix.CONTEXTS))
        ctx = TicketMix.CONTEXTS[key]
        lp = r.int(*ctx['lp'])
        diff = r.int(2, 6)
        n = r.int(60, 240)
        nh = r.int(n // 5, 4 * n // 5)
        x = r.pick(ctx['X'])
        if key == 'play' and x <= n:
            raise Retry
        return dict(who=r.person(), key=key, lp=lp, hp=lp + diff, n=n, nh=nh, x=x, ask_hi=r.chance(0.5))

    fallback = dict(who=person('Omar'), key='play', lp=5, hp=8, n=240, nh=120, x=400, ask_hi=False)

    @staticmethod
    def R(p):
        return p['nh'] * p['hp'] + (p['n'] - p['nh']) * p['lp']

    @staticmethod
    def solve(p):
        R = TicketMix.R(p)
        sols = [h for h in range(p['n'] + 1) if h * p['hp'] + (p['n'] - h) * p['lp'] == R]
        assert len(sols) == 1
        h = sols[0]
        return h if p['ask_hi'] else p['n'] - h

    @staticmethod
    def render(p):
        ctx = TicketMix.CONTEXTS[p['key']]
        w, n, lp, hp, nh = p['who'], p['n'], p['lp'], p['hp'], p['nh']
        R = TicketMix.R(p)
        base = n * lp
        extra = R - base
        diff = hp - lp
        hs, hpl = ctx['hi']
        ls, lpl = ctx['lo']
        x = word(p['x']) if p['x'] <= 20 else num(p['x'])
        stem = _fmt(ctx['stem'], w, n=n, hp=usd(hp * 100), lp=usd(lp * 100), R=usd(R * 100), x=x)
        t = hpl if p['ask_hi'] else lpl
        steps = [
            f"If all {n} were {lpl}, the total would be {n} × {usd(lp * 100)} = {usd(base * 100)}.",
            f"The actual total is {usd(R * 100)} − {usd(base * 100)} = {usd(extra * 100)} more than that.",
            f"Each {hs} brings in {usd(diff * 100)} more than each {ls}, so {hpl}: "
            f"{usd(extra * 100)} ÷ {usd(diff * 100)} = {num(nh)}.",
        ]
        if not p['ask_hi']:
            steps.append(f"{cap(lpl)}: {n} − {nh} = {num(n - nh)}.")
        unit = 'tickets' if p['key'] == 'play' else t if p['key'] == 'wash' else 'plates'
        return dict(stem=stem, ask=_fmt(ctx['ask'], w, t=t), steps=steps, unit=unit)


@template(id='t3.two-year-growth.v1', tier=3, topic='growth', kind='money', seconds=80)
class TwoYearGrowth:
    CONTEXTS = {
        'save': dict(stem="{w} deposited {P} in a savings account that earns {r}% interest, compounded once a "
                          "year. {He} won't add or take out any money. The bank requires a {x} minimum balance.",
                     total="How much will be in the account after 2 years?",
                     gain="How much interest will {w} earn over the 2 years?"),
        'cd': dict(stem="{w}'s grandmother gave {him} {P} for {his} {x} birthday. {He} put all of it in a "
                        "certificate of deposit that pays {r}% interest, compounded once a year, and left it alone.",
                   total="How much will the certificate of deposit be worth after 2 years?",
                   gain="How much interest will the money earn over the 2 years?"),
        'car': dict(stem="{w} bought a used car for {P}. {His} mechanic estimates that the car will lose {r}% of "
                         "its value each year, based on what it is worth at the start of that year. The car gets "
                         "about {x} miles per gallon.",
                    total="Using that estimate, what will the car be worth after 2 years?",
                    gain="Using that estimate, how much value will the car lose over the 2 years?"),
    }

    @staticmethod
    def params(r):
        key = r.pick(['save', 'cd', 'car'])
        if key == 'car':
            P = r.int(6, 24) * 1000
            rate = r.pick([10, 15, 20, 25])
            if rate == 15 and P % 4000:
                raise Retry  # 15% of an odd thousand twice gets ugly (e.g. 15% of $19,550)
            x = r.int(24, 36)
        else:
            P = r.pick([800, 1000, 1200, 1500, 2000, 2400, 2500, 3000, 4000, 5000, 6000, 8000])
            rate = r.pick([2, 3, 4, 5, 6, 8, 10])
            x = r.pick([25, 50, 100]) if key == 'save' else r.int(16, 21)
        sign = -1 if key == 'car' else 1
        if (P * 100 * (100 + sign * rate) ** 2) % 10000:
            raise Retry
        return dict(who=r.person(), key=key, P=P, rate=rate, x=x, gain=r.chance(0.5))

    fallback = dict(who=person('Lena'), key='save', P=2000, rate=5, x=50, gain=False)

    @staticmethod
    def solve(p):
        g = F(100 + (-1 if p['key'] == 'car' else 1) * p['rate'], 100)
        end = p['P'] * 100 * g ** 2
        return abs(end - p['P'] * 100) if p['gain'] else end

    @staticmethod
    def render(p):
        ctx = TwoYearGrowth.CONTEXTS[p['key']]
        w, P, rate = p['who'], p['P'] * 100, p['rate']
        x = usd(p['x'] * 100) if p['key'] == 'save' else ordinal(p['x']) if p['key'] == 'cd' else num(p['x'])
        stem = _fmt(ctx['stem'], w, P=usd(P), r=rate, x=x)
        ask = _fmt(ctx['gain'] if p['gain'] else ctx['total'], w)
        car = p['key'] == 'car'
        i1 = P * rate // 100
        b1 = P - i1 if car else P + i1
        i2 = b1 * rate // 100
        b2 = b1 - i2 if car else b1 + i2
        word_ = 'loses' if car else 'earns'
        sgn = '−' if car else '+'
        steps = [
            f"Year 1: {rate}% of {usd(P)} is {usd(i1)}, so the value goes to {usd(P)} {sgn} {usd(i1)} = {usd(b1)}.",
            f"Year 2: {rate}% of {usd(b1)} is {usd(i2)}, so it goes to {usd(b1)} {sgn} {usd(i2)} = {usd(b2)}.",
        ]
        if p['gain']:
            steps.append(f"Over both years it {word_} {usd(i1)} + {usd(i2)} = {usd(i1 + i2)}.")
        else:
            steps.append(f"After 2 years: {usd(b2)}.")
        return dict(stem=stem, ask=ask, steps=steps)


@template(id='t3.paint-gallons.v1', tier=3, topic='geometry', kind='int', unit='gallons', seconds=85)
class PaintGallons:
    ROOMS = ['bedroom', 'home office', 'basement playroom', 'living room', 'dining room']

    @staticmethod
    def params(r):
        L, W = r.int(10, 20), r.int(8, 16)
        if W >= L:
            raise Retry
        H = r.pick([8, 9, 10])
        cov = r.pick([350, 400])
        skip = r.pick([0, 0, 40, 50, 60])
        total = 2 * (2 * (L + W) * H - skip)
        q = F(total, cov)
        frac_part = q - (q.numerator // q.denominator)
        if not F(1, 10) <= frac_part <= F(9, 10) or q > 10:
            raise Retry
        return dict(who=r.person(), room=r.pick(PaintGallons.ROOMS), L=L, W=W, H=H, cov=cov, skip=skip,
                    price=r.pick([28, 32, 36, 39, 42, 45]))

    fallback = dict(who=person('Ben'), room='bedroom', L=14, W=12, H=8, cov=400, skip=0, price=36)

    @staticmethod
    def solve(p):
        walls = 2 * p['L'] * p['H'] + 2 * p['W'] * p['H'] - p['skip']
        need = 2 * walls
        n = 1
        while n * p['cov'] < need:
            n += 1
        return n

    @staticmethod
    def render(p):
        w, L, W, H, cov, skip = p['who'], p['L'], p['W'], p['H'], p['cov'], p['skip']
        A = 2 * (L + W) * H
        stem = (f"{w} is painting the four walls of {w.his} {p['room']}, which is {L} feet long, {W} feet wide and "
                f"{H} feet high. {w.He} wants two coats on every wall. ")
        if skip:
            stem += f"The door and windows take up {skip} square feet that won't be painted. "
        stem += (f"One gallon of paint covers {cov} square feet with one coat, and the paint costs "
                 f"{usd(p['price'] * 100)} a gallon.")
        ask = f"If paint is sold only in whole gallons, how many gallons does {w} need to buy?"
        steps = [f"Wall area: 2 × ({L} + {W}) × {H} = {num(A)} square feet."]
        if skip:
            steps.append(f"Minus the door and windows: {num(A)} − {skip} = {num(A - skip)} square feet.")
        T = 2 * (A - skip)
        q = F(T, cov)
        n = -(-T // cov)
        steps.append(f"Two coats: {num(A - skip)} × 2 = {num(T)} square feet.")
        approx = '=' if q == F(num(q, 1)) else '≈'
        steps.append(f"{num(T)} ÷ {cov} {approx} {num(q, 1)}, which is more than {n - 1}, so round up to "
                     f"{plural(n, 'gallon')}.")
        return dict(stem=stem, ask=ask, steps=steps)


@template(id='t3.survey-percent.v1', tier=3, topic='data', kind='pct', seconds=70)
class SurveyPercent:
    CONTEXTS = {
        'lunch': dict(options=['Tacos', 'Pasta', 'Pizza', 'Salad bar'], col='Number of students',
                      who='students', X=[3, 4, 5],
                      stem="{w} surveyed the students in {his} grade about their favorite school lunch. Each student "
                           "picked exactly one option, and the table shows the results. {He} collected the answers "
                           "over {x} days."),
        'commute': dict(options=['Drive', 'Bus or train', 'Bike', 'Walk'], col='Number of employees',
                        who='employees', X=[40, 60, 75, 120],
                        stem="{w}'s company asked its employees how they usually get to work. Each person gave "
                             "one answer, shown in the table. The office parking lot has {x} spaces."),
        'library': dict(options=['Borrow books', 'Use computers', 'Attend events', 'Study'],
                        col='Number of visitors', who='visitors', X=[48, 56, 60, 64],
                        stem="{w} works at the town library and asked visitors their main reason for coming in. "
                             "Each visitor gave one answer, shown in the table. The library is open {x} hours a "
                             "week."),
    }

    @staticmethod
    def params(r):
        key = r.pick(sorted(SurveyPercent.CONTEXTS))
        T = r.pick([40, 80, 120, 160, 200, 240])
        u = T // 40
        a, b, c = r.int(2, 18), r.int(2, 18), r.int(2, 18)
        d = 40 - a - b - c
        if d < 2 or len({a, b, c, d}) < 4:
            raise Retry
        parts = r.shuffle([a, b, c, d])
        counts = [k * u for k in parts]
        mode = r.pick(['one', 'two', 'not'])
        if mode == 'two':
            sel = sorted(r.sample(range(4), 2))
        else:
            sel = [r.int(0, 3)]
        return dict(who=r.person(), key=key, counts=counts, mode=mode, sel=sel,
                    x=r.pick(SurveyPercent.CONTEXTS[key]['X']))

    fallback = dict(who=person('Grace'), key='lunch', counts=[45, 30, 27, 18], mode='two', sel=[0, 3], x=4)

    @staticmethod
    def solve(p):
        T = sum(p['counts'])
        chosen = [i for i in range(4) if (i in p['sel']) != (p['mode'] == 'not')]
        return F(sum(p['counts'][i] for i in chosen) * 100, T)

    @staticmethod
    def render(p):
        ctx = SurveyPercent.CONTEXTS[p['key']]
        w, counts, opts = p['who'], p['counts'], ctx['options']
        T = sum(counts)
        stem = _fmt(ctx['stem'], w, x=word(p['x']) if p['x'] <= 10 else num(p['x']))
        table = dict(headers=['Answer', ctx['col']], rows=[[o, c] for o, c in zip(opts, counts)])
        who = ctx['who']
        q = lambda i: f'"{opts[i]}"'
        steps = [f"Total surveyed: {' + '.join(str(c) for c in counts)} = {T}."]
        if p['mode'] == 'one':
            i = p['sel'][0]
            s = counts[i]
            ask = f"What percent of the {who} surveyed chose {q(i)}?"
            steps.append(f"{q(i)} was chosen by {s} {who}.")
        elif p['mode'] == 'two':
            i, j = p['sel']
            s = counts[i] + counts[j]
            ask = f"What percent of the {who} surveyed chose either {q(i)} or {q(j)}?"
            steps.append(f"{q(i)} or {q(j)}: {counts[i]} + {counts[j]} = {s} {who}.")
        else:
            i = p['sel'][0]
            s = T - counts[i]
            ask = f"What percent of the {who} surveyed did not choose {q(i)}?"
            steps.append(f"Everyone except {q(i)}: {T} − {counts[i]} = {s} {who}.")
        f = F(s, T)
        steps.append(f"{s} ÷ {T} = {frac(f)} = {pct(f * 100)}.")
        return dict(stem=stem, ask=ask, steps=steps, table=table)


@template(id='t3.unit-price-gap.v1', tier=3, topic='money', kind='int', unit='cents', seconds=80)
class UnitPriceGap:
    CONTEXTS = {
        'cereal': dict(thing='box of the same cereal', u='ounces', ab='oz', sizes=[10, 12, 16, 20, 24, 32],
                       cpo=(12, 30), stem="{w} is comparing three sizes of the same cereal, shown in the table. "
                                          "{He} eats about {x} ounces each morning."),
        'pb': dict(thing='jar of peanut butter', u='ounces', ab='oz', sizes=[12, 16, 20, 24, 32, 40],
                   cpo=(10, 25), stem="{w} is stocking up on peanut butter and compares the three jar sizes in the "
                                      "table. {He} goes through about {x} jars a month."),
        'soap': dict(thing='bottle of laundry detergent', u='fluid ounces', ab='fl oz', sizes=[32, 40, 50, 80, 100],
                     cpo=(8, 20), stem="{w} is buying laundry detergent. The store sells the same brand in the three "
                                       "sizes shown in the table. {He} does about {x} loads of laundry a week."),
        'oil': dict(thing='bottle of olive oil', u='fluid ounces', ab='fl oz', sizes=[8, 12, 16, 24, 32],
                    cpo=(25, 60), stem="{w} cooks with olive oil almost every night. {His} grocery store sells it in "
                                       "the three bottle sizes shown in the table, and {he} usually shops on {x}."),
    }
    X = {'cereal': [2, 3, 4], 'pb': [2, 3], 'soap': [3, 4, 5, 6], 'oil': ['Sundays', 'Saturdays', 'Mondays']}

    @staticmethod
    def params(r):
        key = r.pick(sorted(UnitPriceGap.CONTEXTS))
        ctx = UnitPriceGap.CONTEXTS[key]
        sizes = sorted(r.sample(ctx['sizes'], 3))
        cpos = [r.int(*ctx['cpo']) for _ in range(3)]
        if len(set(cpos)) < 3 or max(cpos) - min(cpos) < 2 or max(cpos) - min(cpos) > 12:
            raise Retry
        if cpos[2] == min(cpos) and r.chance(0.3):
            raise Retry  # don't always let the biggest size win
        prices = [s * c for s, c in zip(sizes, cpos)]
        if max(prices) > 3000 or not prices[0] < prices[1] < prices[2]:
            raise Retry
        return dict(who=r.person(), key=key, sizes=sizes, prices=prices, x=r.pick(UnitPriceGap.X[key]))

    fallback = dict(who=person('Kenji'), key='cereal', sizes=[12, 16, 24], prices=[348, 416, 576], x=2)

    @staticmethod
    def solve(p):
        per = [F(c, s) for s, c in zip(p['sizes'], p['prices'])]
        return max(per) - min(per)

    @staticmethod
    def render(p):
        ctx = UnitPriceGap.CONTEXTS[p['key']]
        w, sizes, prices = p['who'], p['sizes'], p['prices']
        x = p['x'] if isinstance(p['x'], str) else word(p['x'])
        stem = _fmt(ctx['stem'], w, x=x)
        names = ['Small', 'Medium', 'Large']
        table = dict(headers=['Size', 'Amount', 'Price'],
                     rows=[[n, f"{s} {ctx['ab']}", usd2(c)] for n, s, c in zip(names, sizes, prices)])
        per = [c // s for s, c in zip(sizes, prices)]
        steps = [f"{n}: {usd2(c)} ÷ {s} = {cp}¢ per {'fluid ounce' if 'fluid' in ctx['u'] else 'ounce'}."
                 for n, s, c, cp in zip(names, sizes, prices, per)]
        steps.append(f"Highest minus lowest: {max(per)}¢ − {min(per)}¢ = {plural(max(per) - min(per), 'cent')}.")
        unit_word = 'fluid ounce' if 'fluid' in ctx['u'] else 'ounce'
        ask = (f"What is the difference, in cents, between the highest and lowest price per {unit_word} among "
               f"the three sizes?")
        return dict(stem=stem, ask=ask, steps=steps, table=table)


@template(id='t3.meal-total.v1', tier=3, topic='money', kind='money', seconds=80)
class MealTotal:
    CONTEXTS = {
        'dinner': dict(stem="{w} and {k} friends went out for dinner and waited {x} minutes for a table. They "
                            "ordered {a} entrées at {p1} each and one appetizer to share for {p2}.",
                       ask="What was the total cost of the dinner, including tax and tip?", X=[15, 20, 25, 30]),
        'brunch': dict(stem="{w} took {his} family out for brunch at a diner that opened {x} years ago. They "
                            "ordered {a} pancake plates at {p1} each and a pitcher of orange juice for {p2}.",
                       ask="What was the total cost of the brunch, including tax and tip?", X=[12, 20, 25, 40]),
        'lunch': dict(stem="{w} ordered lunch from a café for a team meeting that ran {x} minutes. The order was "
                           "{a} sandwich boxes at {p1} each plus a fruit tray for {p2}.",
                      ask="What was the total cost of the lunch order, including tax and tip?", X=[45, 60, 90]),
    }

    @staticmethod
    def params(r):
        key = r.pick(sorted(MealTotal.CONTEXTS))
        a = r.int(2, 6)
        p1 = r.int(9, 22)
        p2 = r.int(6, 15)
        S = a * p1 + p2
        if not 30 <= S <= 120:
            raise Retry
        return dict(who=r.person(), key=key, a=a, p1=p1, p2=p2, tax=r.pick([5, 6, 8, 10]), tip=r.pick([15, 20]),
                    x=r.pick(MealTotal.CONTEXTS[key]['X']))

    fallback = dict(who=person('Hana'), key='dinner', a=4, p1=14, p2=8, tax=8, tip=20, x=20)

    @staticmethod
    def solve(p):
        S = F(p['a'] * p['p1'] + p['p2'])
        return S * (100 + p['tax'] + p['tip'])  # in cents: S dollars * (1 + rates) * 100

    @staticmethod
    def render(p):
        ctx = MealTotal.CONTEXTS[p['key']]
        w, a, p1, p2, tax, tip = p['who'], p['a'], p['p1'], p['p2'], p['tax'], p['tip']
        S = (a * p1 + p2) * 100
        stem = _fmt(ctx['stem'], w, k=word(a - 1), a=word(a), p1=usd(p1 * 100), p2=usd(p2 * 100), x=p['x'])
        payer = w.he if p['key'] == 'lunch' else 'they'
        stem += (f" Sales tax is {tax}%, and {payer} added a {tip}% tip figured on the food cost before tax.")
        T = S * tax // 100
        P = S * tip // 100
        if tip == 15:
            tip_step = (f"Tip: 10% of {usd(S)} is {usd(S // 10)}, plus half of that, {usd(S // 20)}, "
                        f"gives {usd(P)}.")
        else:
            tip_step = f"Tip: 20% of {usd(S)} = 2 × {usd(S // 10)} = {usd(P)}."
        steps = [
            f"Food cost: {a} × {usd(p1 * 100)} + {usd(p2 * 100)} = {usd(S)}.",
            f"Tax: {tax}% of {usd(S)} = {usd(T)}.",
            tip_step,
            f"Total: {usd(S)} + {usd(T)} + {usd(P)} = {usd(S + T + P)}.",
        ]
        return dict(stem=stem, ask=ctx['ask'], steps=steps)


@template(id='t3.tank-gallons.v1', tier=3, topic='units', kind='dec', unit='gallons', seconds=80)
class TankGallons:
    CONTEXTS = {
        'aquarium': dict(stem="{w} bought a rectangular glass aquarium that is {L} inches long, {W} inches wide and "
                              "{H} inches tall. {He} plans to keep {x} small fish in it.",
                         dims=([24, 30, 36, 48], [12, 18], [12, 18, 24]), inches=True, X=[6, 8, 10, 12]),
        'trough': dict(stem="The water trough at {w}'s farm is a rectangular metal tank {L} feet long, {W} feet "
                            "wide and {H} feet deep. It serves the {x} horses in the north pasture.",
                       dims=([4, 5, 6, 8], [2, F(5, 2), 3], [F(3, 2), 2]), inches=False, X=[3, 4, 5, 6]),
        'pond': dict(stem="{w} built a rectangular backyard pond that is {L} feet long, {W} feet wide and {H} feet "
                          "deep, and {he} stocked it with {x} goldfish.",
                     dims=([6, 8, 10, 12], [3, 4, 5, 6], [F(3, 2), 2, F(5, 2)]), inches=False, X=[7, 9, 12, 15]),
    }

    @staticmethod
    def params(r):
        key = r.pick(sorted(TankGallons.CONTEXTS))
        ctx = TankGallons.CONTEXTS[key]
        L, W, H = (r.pick(d) for d in ctx['dims'])
        if W >= L:
            raise Retry
        k = 12 if ctx['inches'] else 1
        V = F(L, k) * F(W, k) * F(H, k)
        if V.denominator != 1 or V > 200:
            raise Retry
        return dict(who=r.person(), key=key, L=L, W=W, H=H, x=r.pick(ctx['X']))

    fallback = dict(who=person('Theo'), key='aquarium', L=36, W=12, H=24, x=8)

    @staticmethod
    def solve(p):
        # cubic inches -> gallons via 1728 cubic inches per cubic foot
        k = 1728 if TankGallons.CONTEXTS[p['key']]['inches'] else 1
        return F(p['L']) * p['W'] * p['H'] / k * F(15, 2)

    @staticmethod
    def render(p):
        ctx = TankGallons.CONTEXTS[p['key']]
        w, L, W, H = p['who'], F(p['L']), F(p['W']), F(p['H'])
        stem = _fmt(ctx['stem'], w, L=num(L), W=num(W), H=num(H), x=word(p['x']))
        stem += " One cubic foot holds about 7.5 gallons of water."
        ask = (f"Using 7.5 gallons per cubic foot, how many gallons of water does the "
               f"{'aquarium' if p['key'] == 'aquarium' else 'trough' if p['key'] == 'trough' else 'pond'} "
               f"hold when completely full?")
        steps = []
        if ctx['inches']:
            L, W, H = L / 12, W / 12, H / 12
            steps.append(f"Convert to feet (÷ 12): {num(p['L'])} in = {num(L)} ft, {num(p['W'])} in = {num(W)} ft, "
                         f"{num(p['H'])} in = {num(H)} ft.")
        V = L * W * H
        steps.append(f"Volume: {num(L)} × {num(W)} × {num(H)} = {num(V)} cubic feet.")
        steps.append(f"Gallons: {num(V)} × 7.5 = {num(V * F(15, 2))}.")
        return dict(stem=stem, ask=ask, steps=steps)


@template(id='t3.payment-plan.v1', tier=3, topic='money', kind='money', seconds=70)
class PaymentPlan:
    CONTEXTS = [
        ('laptop', 'an electronics store', (500, 1400), "The laptop weighs about {x} pounds.", [3, 4, 5]),
        ('couch', 'a furniture store', (600, 1500), "The couch is {x} inches long.", [72, 84, 90]),
        ('refrigerator', 'an appliance store', (700, 1600), "The store delivers for free within {x} miles.",
         [15, 20, 25, 30]),
        ('electric bike', 'a bike shop', (800, 1600), "Its battery can go about {x} miles on one charge.",
         [30, 40, 50]),
    ]

    @staticmethod
    def params(r):
        ci = r.int(0, len(PaymentPlan.CONTEXTS) - 1)
        lo, hi = PaymentPlan.CONTEXTS[ci][2]
        m = r.pick([6, 10, 12, 18, 24])
        pay = r.int(25, 250)
        if m >= 10 and pay >= 100:
            raise Retry
        down = r.pick([50, 75, 100, 150, 200])
        extra = r.int(6, 50) * 5
        cash = down + m * pay - extra
        if not lo <= cash <= hi:
            raise Retry
        return dict(who=r.person(), ci=ci, m=m, pay=pay, down=down, cash=cash,
                    x=r.pick(PaymentPlan.CONTEXTS[ci][4]))

    fallback = dict(who=person('Sam'), ci=0, m=12, pay=70, down=90, cash=840, x=4)

    @staticmethod
    def solve(p):
        total = p['down'] + sum(p['pay'] for _ in range(p['m']))
        return (total - p['cash']) * 100

    @staticmethod
    def render(p):
        item, store, _, irr, _ = PaymentPlan.CONTEXTS[p['ci']]
        w, m, pay, down, cash = p['who'], p['m'], p['pay'] * 100, p['down'] * 100, p['cash'] * 100
        art = 'an' if item[0] in 'aeiou' else 'a'
        stem = (f"{w} wants to buy {art} {item} at {store}. The price is {usd(cash)} if {w.he} pays all at once. "
                f"The store also offers a payment plan: {usd(down)} down, then {m} monthly payments of {usd(pay)}. "
                + irr.format(x=p['x']))
        M = m * pay
        steps = [
            f"Monthly payments: {m} × {usd(pay)} = {usd(M)}.",
            f"Payment plan total: {usd(down)} + {usd(M)} = {usd(down + M)}.",
            f"Extra cost: {usd(down + M)} − {usd(cash)} = {usd(down + M - cash)}.",
        ]
        ask = f"How much more would {w} pay in total with the payment plan than by paying all at once?"
        return dict(stem=stem, ask=ask, steps=steps)


# =====================================================================================  TIER 4


@template(id='t4.work-together.v1', tier=4, topic='rates', kind='dec', unit='hours', seconds=90)
class WorkTogether:
    CONTEXTS = {
        'fence': dict(unit='hours', two=True, X=[80, 120, 150, 200],
                      stem="{a} and {b} are painting the fence around their community garden. Working alone, {a} "
                           "could paint it in {x1} hours, and {b} could paint it in {y1} hours. The fence is {X} "
                           "feet long.",
                      ask="If they work together, each at a steady pace, how many hours will the fence take?"),
        'pool': dict(unit='minutes', two=False, X=[300, 400, 500, 600],
                     stem="{w} is filling an inflatable pool with two hoses. The garden hose alone would fill it in "
                          "{x1} minutes, and the hose from the side of the house alone would take {y1} minutes. "
                          "The pool holds about {X} gallons.",
                     ask="With both hoses running at full flow, how many minutes will it take to fill the empty "
                         "pool?"),
        'print': dict(unit='minutes', two=False, X=[3, 4, 5],
                      stem="{w}'s office needs a big stack of training booklets printed by {X} o'clock. The new "
                           "printer could print the whole job alone in {x1} minutes, and the old printer alone "
                           "would take {y1} minutes.",
                      ask="If the two printers split the job and run at the same time, how many minutes will it "
                          "take?"),
    }

    @staticmethod
    def params(r):
        key = r.pick(sorted(WorkTogether.CONTEXTS))
        ctx = WorkTogether.CONTEXTS[key]
        if ctx['unit'] == 'hours':
            x, y = r.int(2, 12), r.int(3, 30)
        else:
            x, y = r.int(12, 90), r.int(15, 180)
        if y <= x or y > 4 * x or _lcm(x, y) > 360:
            raise Retry
        T = F(x * y, x + y)
        if ctx['unit'] == 'hours':
            if (T * 10).denominator != 1 or T < 1:
                raise Retry
        elif T.denominator != 1 or T < 8:
            raise Retry
        ppl = r.people(2) if ctx['two'] else [r.person()]
        return dict(who=ppl, key=key, x=x, y=y, X=r.pick(ctx['X']))

    fallback = dict(who=[person('Ava'), person('Felix')], key='fence', x=6, y=12, X=120)

    @staticmethod
    def solve(p):
        return F(p['x'] * p['y'], p['x'] + p['y'])

    @staticmethod
    def render(p):
        ctx = WorkTogether.CONTEXTS[p['key']]
        x, y = p['x'], p['y']
        if ctx['two']:
            a, b = p['who']
            stem = ctx['stem'].format(a=a, b=b, x1=x, y1=y, X=p['X'])
            na, nb = a.name, b.name
            per = 'hour'
            job = 'the fence'
        else:
            w = p['who'][0]
            stem = _fmt(ctx['stem'], w, x1=x, y1=y, X=p['X'])
            na, nb = ('the garden hose', 'the other hose') if p['key'] == 'pool' else ('the new printer',
                                                                                    'the old printer')
            per = 'minute'
            job = 'the job'
        L = _lcm(x, y)
        s = F(1, x) + F(1, y)
        steps = [
            f"In one {per}, {na} does 1/{x} of {job} and {nb} does 1/{y}.",
            f"Together: 1/{x} + 1/{y} = {L // x}/{L} + {L // y}/{L} = {L // x + L // y}/{L}"
            + (f" = {frac(s)}" if F(L // x + L // y, L).denominator != L else '') + f" of {job} per {per}.",
            f"Time: 1 ÷ {frac(s)} = " + (f"{frac(1 / s)} = " if (1 / s).denominator > 1 else '')
            + f"{num(1 / s)} {ctx['unit']}.",
        ]
        return dict(stem=stem, ask=ctx['ask'], steps=steps, unit=ctx['unit'])


@template(id='t4.right-triangle.v1', tier=4, topic='geometry', kind='int', unit='feet', seconds=90)
class RightTriangle:
    TRIPLES = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (20, 21, 29)]

    @staticmethod
    def params(r):
        key = r.pick(['ladder', 'park', 'gate'])
        a, b, c = r.pick(RightTriangle.TRIPLES if key == 'gate' else RightTriangle.TRIPLES[:4])
        if key == 'ladder':
            k = r.pick([1, 2, 3, 4, 5])
            a, b, c = a * k, b * k, c * k
            if not 10 <= c <= 30 or a * 2 > b:
                raise Retry
            x = r.pick([225, 250, 300])
        elif key == 'park':
            k = r.pick([10, 20, 30, 40, 50, 60, 80, 100, 150, 200, 250, 300])
            a, b, c = a * k, b * k, c * k
            if not 300 <= b <= 1200 or (c >= 1000 and c % 100):
                raise Retry
            x = r.int(8, 20)
        else:
            k = r.pick([1, 2, 3, 4, 6, 8, 10, 12])
            a, b, c = a * k, b * k, c * k
            if not 30 <= a <= 60 or not 36 <= b <= 72:
                raise Retry
            x = r.pick([2, 3])
        return dict(who=r.person(), key=key, a=a, b=b, c=c, x=x)

    fallback = dict(who=person('Marcus'), key='ladder', a=5, b=12, c=13, x=250)

    @staticmethod
    def solve(p):
        a, b, c = p['a'], p['b'], p['c']
        if p['key'] == 'ladder':
            return next(h for h in range(1, c) if h * h + a * a == c * c)
        if p['key'] == 'park':
            return a + b - isqrt(a * a + b * b)
        return isqrt(a * a + b * b)

    @staticmethod
    def render(p):
        w, a, b, c, key = p['who'], p['a'], p['b'], p['c'], p['key']
        if key == 'ladder':
            stem = (f"{w} leans {a_an(c)}-foot ladder against the side of {w.his} house to clean the gutters. For "
                    f"safety, the bottom of the ladder sits {a} feet out from the wall, on level ground. The "
                    f"ladder is rated to hold {p['x']} pounds.")
            ask = "How high up the wall does the top of the ladder reach, in feet?"
            steps = [
                "The wall, the ground and the ladder form a right triangle, with the ladder as the hypotenuse.",
                f"height² = {c}² − {a}² = {num(c * c)} − {num(a * a)} = {num(b * b)}.",
                f"height = √{num(b * b)} = {b} feet.",
            ]
            unit = 'feet'
        elif key == 'park':
            stem = (f"A rectangular park near {w}'s apartment is {num(b)} meters long and {num(a)} meters wide. "
                    f"{w} usually walks along two edges to get from one corner to the opposite corner. Today {w.he} "
                    f"cuts straight across the grass on the diagonal instead. The park has {p['x']} benches.")
            ask = "How many meters shorter is the diagonal route than the route along the two edges?"
            g = gcd(a, b)
            pa, pb, pc = a // g, b // g, c // g
            steps = [
                f"Along the edges: {num(b)} + {num(a)} = {num(a + b)} meters.",
                f"Shrink the numbers first: {num(b)} = {g} × {pb} and {num(a)} = {g} × {pa}. Since {pb}² + {pa}² = "
                f"{pb * pb} + {pa * pa} = {pc * pc} = {pc}², the diagonal is {g} × {pc} = {num(c)} meters.",
                f"Savings: {num(a + b)} − {num(c)} = {num(a + b - c)} meters.",
            ]
            unit = 'meters'
        else:
            stem = (f"{w} is building a wooden garden gate shaped like a rectangle, {a} inches wide and {b} inches "
                    f"tall. To keep it from sagging, {w.he} will nail a straight brace from one corner to the "
                    f"opposite corner. The gate will hang on {word(p['x'])} hinges.")
            ask = "How long must the brace be, in inches?"
            g = gcd(a, b)
            pa, pb, pc = a // g, b // g, c // g
            steps = ["The brace is the hypotenuse of a right triangle with legs equal to the width and height."]
            if g > 1:
                steps += [f"Shrink the numbers first: {a} = {g} × {pa} and {b} = {g} × {pb}.",
                          f"{pa}² + {pb}² = {pa * pa} + {pb * pb} = {pc * pc} = {pc}², so the brace is "
                          f"{g} × {pc} = {c} inches."]
            else:
                steps += [f"brace² = {a}² + {b}² = {num(a * a)} + {num(b * b)} = {num(c * c)}.",
                          f"brace = √{num(c * c)} = {c} inches."]
            unit = 'inches'
        return dict(stem=stem, ask=ask, steps=steps, unit=unit)


@template(id='t4.break-even.v1', tier=4, topic='algebra', kind='int', unit='visits', seconds=95)
class BreakEven:
    @staticmethod
    def params(r):
        key = r.pick(['gym', 'car', 'pottery'])
        if key == 'gym':
            n = r.int(6, 30)
            rd = r.int(2, 8)
            r1 = r.int(4, 12)
            F2 = r.pick([0, 0, 10, 15, 20])
            F1 = F2 + n * rd
            if F1 > 200 or F1 % 5:
                raise Retry
            return dict(who=r.person(), key=key, n=n, F1=F1 * 100, F2=F2 * 100, r1=r1 * 100, r2=(r1 + rd) * 100,
                        x=r.pick([9, 10, 11]))
        if key == 'car':
            rd = r.pick([5, 10, 15, 20, 25])
            Fd = r.int(5, 40)
            if (Fd * 100) % rd:
                raise Retry
            n = Fd * 100 // rd
            if not 60 <= n <= 400 or n % 10:
                raise Retry
            r1 = r.pick([10, 15, 20, 25, 30])
            F2 = r.int(25, 50)
            return dict(who=r.person(), key=key, n=n, F1=(F2 + Fd) * 100, F2=F2 * 100, r1=r1, r2=r1 + rd,
                        x=r.pick(['7:30 a.m.', '8 a.m.', '9:15 a.m.']))
        n = r.int(3, 10)
        rd = r.int(4, 12)
        r1 = r.int(8, 15)
        F1 = n * rd
        if F1 % 5 or F1 > 90:
            raise Retry
        return dict(who=r.person(), key=key, n=n, F1=F1 * 100, F2=0, r1=r1 * 100, r2=(r1 + rd) * 100,
                    x=r.pick([90, 120, 150]))

    fallback = dict(who=person('Imani'), key='gym', n=12, F1=6000, F2=0, r1=400, r2=900, x=10)

    @staticmethod
    def solve(p):
        return next(n for n in range(1, 5000) if p['F1'] + n * p['r1'] == p['F2'] + n * p['r2'])

    @staticmethod
    def render(p):
        w, key, n = p['who'], p['key'], p['n']
        F1, F2, r1, r2 = p['F1'], p['F2'], p['r1'], p['r2']
        if key == 'gym':
            names, per, unit = ('Member plan', 'Basic plan'), 'visit', 'visits'
            table = dict(headers=['Plan', 'One-time fee', 'Cost per visit'],
                         rows=[[names[0], usd(F1), usd(r1)], [names[1], usd(F2), usd(r2)]])
            stem = (f"{w} wants to start going to a climbing gym and is choosing between the two plans in the "
                    f"table. The gym is open until {p['x']} o'clock on weeknights.")
            ask = "For how many visits would the two plans cost exactly the same?"
        elif key == 'car':
            names, per, unit = ('Company A', 'Company B'), 'mile', 'miles'
            table = dict(headers=['Company', 'Daily fee', 'Cost per mile'],
                         rows=[[names[0], usd(F1), usd(r1)], [names[1], usd(F2), usd(r2)]])
            stem = (f"{w} needs a rental car for one day and is comparing the two companies in the table. {w.He} "
                    f"plans to pick up the car at {p['x']} on Friday.")
            ask = "For how many miles of driving would the two companies charge exactly the same amount?"
        else:
            names, per, unit = ('Membership', 'Drop-in'), 'class', 'classes'
            table = dict(headers=['Option', 'Monthly fee', 'Cost per class'],
                         rows=[[names[0], usd(F1), usd(r1)], [names[1], usd(F2), usd(r2)]])
            stem = (f"{w} is signing up for pottery classes at a local studio, which offers the two options in "
                    f"the table. Each class lasts {p['x']} minutes.")
            ask = "How many classes in a month would make the two options cost exactly the same?"
        fd, rd = F1 - F2, r2 - r1
        if key == 'car':
            div = f"{num(fd)}¢ ÷ {rd}¢ = {num(n)}"
        else:
            div = f"{usd(fd)} ÷ {usd(rd)} = {num(n)}"
        steps = [
            f"{names[0]} costs {usd(fd)} more up front.",
            f"{names[1]} costs {usd(rd)} more per {per}, so each {per} closes the gap by {usd(rd)}.",
            f"The gap closes after {div} {unit}.",
            f"Check: {usd(F1)} + {num(n)} × {usd(r1)} = {usd(F1 + n * r1)} and {usd(F2)} + {num(n)} × {usd(r2)} = "
            f"{usd(F2 + n * r2)}, so the answer is {num(n)} {unit}.",
        ]
        return dict(stem=stem, ask=ask, steps=steps, table=table, unit=unit)


@template(id='t4.doubling-halving.v1', tier=4, topic='growth', kind='dec', unit='bacteria', seconds=85)
class DoublingHalving:
    @staticmethod
    def params(r):
        key = r.pick(['bacteria', 'algae', 'medicine', 'isotope'])
        if key == 'bacteria':
            N0 = r.pick([100, 150, 200, 250, 300, 400, 500, 600, 750, 800])
            d = r.pick([15, 20, 30])
            k = r.int(3, 7)
            if (k * d) % 30 or N0 * 2 ** k > 60000:
                raise Retry
            return dict(who=r.person(), key=key, N0=N0, d=d, k=k, x=r.pick([9, 10, 15]))
        if key == 'algae':
            N0 = r.pick([3, 5, 6, 8, 10, 12, 15, 20, 25])
            d = r.pick([2, 3, 4, 5])
            k = r.int(3, 6)
            if N0 * 2 ** k > 1000:
                raise Retry
            return dict(who=r.person(), key=key, N0=N0, d=d, k=k, x=r.pick([4, 5, 6]))
        N0 = r.pick([200, 240, 250, 300, 320, 400, 480, 500, 600, 640, 800, 960])
        d = r.pick([2, 3, 4, 5, 6, 8]) if key == 'medicine' else r.pick([3, 4, 5, 6, 7, 8, 10, 12])
        k = r.int(2, 5)
        end = F(N0, 2 ** k)
        if (end * 1000).denominator != 1 or end < 5 or (key == 'isotope' and end.denominator != 1):
            raise Retry
        x = r.pick(['7:30 a.m.', '8:15 a.m.', '6:45 p.m.']) if key == 'medicine' else r.pick([12, 15, 20])
        return dict(who=r.person(), key=key, N0=N0, d=d, k=k, x=x)

    fallback = dict(who=person('Nadia'), key='bacteria', N0=400, d=20, k=6, x=10)

    @staticmethod
    def solve(p):
        key, N0, d, k = p['key'], p['N0'], p['d'], p['k']
        if key in ('bacteria', 'algae'):
            amt = F(N0)
            for _ in range(k):
                amt *= 2
            return amt
        if key == 'medicine':
            return F(N0) * F(1, 2) ** k
        end = F(N0, 2 ** k)
        amt, t = F(N0), 0
        while amt > end:
            amt /= 2
            t += d
        return F(t)

    @staticmethod
    def render(p):
        w, key, N0, d, k = p['who'], p['key'], p['N0'], p['d'], p['k']
        chain = lambda vals: ' → '.join(num(v) for v in vals)
        if key == 'bacteria':
            T = F(k * d, 60)
            stem = (f"{w} is growing bacteria for a biology lab. {w.He} starts a dish with {num(N0)} bacteria, and "
                    f"under these conditions the population doubles every {d} minutes. The dish is {p['x']} "
                    f"centimeters across.")
            ask = f"How many bacteria will be in the dish after {plural(T, 'hour')}?"
            vals = [N0 * 2 ** i for i in range(k + 1)]
            steps = [f"{plural(T, 'hour')} = {k * d} minutes, which is {k * d} ÷ {d} = {k} doublings.",
                     f"Double {word(k)} times: {chain(vals)} bacteria."]
            unit = 'bacteria'
        elif key == 'algae':
            T = k * d
            stem = (f"Algae is spreading across the pond on {w}'s farm. Right now it covers {N0} square feet, and "
                    f"the area it covers doubles every {d} days. The pond is about {p['x']} feet deep.")
            ask = f"If it keeps doubling at this rate, how many square feet will the algae cover {T} days from now?"
            vals = [N0 * 2 ** i for i in range(k + 1)]
            steps = [f"{T} days ÷ {d} days = {k} doublings.",
                     f"Double {word(k)} times: {chain(vals)} square feet."]
            unit = 'square feet'
        elif key == 'medicine':
            T = k * d
            stem = (f"{w} takes {a_an(N0)}-milligram dose of a medicine at {p['x']} with a glass of water. The amount of "
                    f"the medicine in the body drops by half every {d} hours.")
            ask = f"How many milligrams of the medicine are left in {w.his} body {T} hours after the dose?"
            vals = [F(N0, 2 ** i) for i in range(k + 1)]
            steps = [f"{T} hours ÷ {d} hours = {k} halvings.",
                     f"Halve {word(k)} times: {chain(vals)} milligrams."]
            unit = 'milligrams'
        else:
            end = N0 // 2 ** k
            stem = (f"{w} is studying {a_an(N0)}-gram sample of a radioactive substance in a lab. The substance has a "
                    f"half-life of {d} days, which means half of whatever is left decays every {d} days. The "
                    f"sample is stored in a case that weighs {p['x']} pounds.")
            ask = f"How many days will it take until only {end} grams of the substance remain?"
            vals = [N0 // 2 ** i for i in range(k + 1)]
            steps = [f"Halve until {end} grams remain: {chain(vals)}. That is {k} halvings.",
                     f"Each halving takes {d} days: {k} × {d} = {k * d} days."]
            unit = 'days'
        return dict(stem=stem, ask=ask, steps=steps, unit=unit)


@template(id='t4.dilute-mix.v1', tier=4, topic='ratio', kind='dec', unit='cups', seconds=95)
class DiluteMix:
    CONTEXTS = {
        'punch': dict(unit='cups', what='juice', V=(4, 16), X=list(range(8, 21)),
                      stem="{w} mixed {V} cups of fruit punch that is {c1}% juice for a party. It tastes too sweet, "
                           "so {he} wants to add water until the punch is only {c2}% juice. {X} guests are coming.",
                      ask="How many cups of water should {w} add?"),
        'spray': dict(unit='ounces', what='vinegar', V=(8, 48), X=list(range(6, 16)),
                      stem="{w} has {V} ounces of a cleaning spray that is {c1}% vinegar. For washing windows, {he} "
                           "wants a weaker spray that is only {c2}% vinegar, so {he}'ll add water. {He} has {X} "
                           "windows to clean.",
                      ask="How many ounces of water should {w} add?"),
        'plant': dict(unit='liters', what='concentrate', V=(2, 12), X=list(range(3, 9)),
                      stem="{w} mixed {V} liters of liquid plant food that is {c1}% concentrate. The label says "
                           "seedlings need a mix that is only {c2}% concentrate, so {he} will dilute it with water. "
                           "{He} is growing {X} trays of seedlings.",
                      ask="How many liters of water should {w} add?"),
    }

    @staticmethod
    def params(r):
        key = r.pick(sorted(DiluteMix.CONTEXTS))
        ctx = DiluteMix.CONTEXTS[key]
        V = r.int(*ctx['V'])
        c1 = r.pick([10, 15, 20, 25, 30, 40, 50, 60])
        c2 = r.pick([4, 5, 8, 10, 12, 15, 20, 25, 30])
        if c2 >= c1 or c1 > 3 * c2:
            raise Retry
        pure = F(V * c1, 100)
        total = pure * 100 / c2
        water = total - V
        if (pure * 10).denominator != 1 or (water * 2).denominator != 1 or water <= 1:
            raise Retry
        x = r.pick(ctx['X'])
        if water in (V, c1, c2, x) and r.chance(0.8):
            raise Retry  # keep the answer from echoing a number in the stem
        return dict(who=r.person(), key=key, V=V, c1=c1, c2=c2, x=x)

    fallback = dict(who=person('Leah'), key='punch', V=12, c1=30, c2=20, x=12)

    @staticmethod
    def solve(p):
        # find w with (V*c1) / (V + w) = c2, searching half-units
        V, c1, c2 = p['V'], p['c1'], p['c2']
        h = 1
        while F(V * c1, 1) / (V + F(h, 2)) > c2:
            h += 1
        assert F(V * c1) / (V + F(h, 2)) == c2
        return F(h, 2)

    @staticmethod
    def render(p):
        ctx = DiluteMix.CONTEXTS[p['key']]
        w, V, c1, c2, u = p['who'], p['V'], p['c1'], p['c2'], ctx['unit']
        X = cap(word(p['x'])) if p['key'] == 'punch' else word(p['x'])
        stem = _fmt(ctx['stem'], w, V=V, c1=c1, c2=c2, X=X)
        pure = F(V * c1, 100)
        total = pure * 100 / c2
        steps = [
            f"{cap(ctx['what'])} now: {c1}% of {V} = {num(pure)} {u}.",
            f"Adding water doesn't change that amount, so for it to be only {c2}% of the mix, the total must grow by "
            f"a factor of {c1}/{c2} = {frac(F(c1, c2))}: {V} × {frac(F(c1, c2))} = {num(total)} {u}.",
            f"Water to add: {num(total)} − {V} = {num(total - V)} {u}.",
        ]
        return dict(stem=stem, ask=_fmt(ctx['ask'], w), steps=steps, unit=u)


@template(id='t4.round-trip-speed.v1', tier=4, topic='rates', kind='dec', unit='miles per hour', seconds=90)
class RoundTripSpeed:
    CONTEXTS = {
        'drive': dict(fast=(40, 75), slow=(30, 60), D=(60, 300), X=[25, 28, 30, 32, 35]),
        'bike': dict(fast=(10, 24), slow=(5, 15), D=(6, 40), X=[2, 3]),
        'kayak': dict(fast=(3, 8), slow=(2, 5), D=(2, 12), X=[10, 12, 14]),
    }

    @staticmethod
    def _combos(key):
        """Every (fast, slow, distance) where each leg is a whole number of quarter hours, the total time
        is a whole number of hours (so 2D ÷ total is easy), and the answer has at most one decimal."""
        ctx = RoundTripSpeed.CONTEXTS[key]
        step = 5 if key == 'drive' else 1
        out = []
        for a in range(ctx['fast'][0], ctx['fast'][1] + 1, step):
            for b in range(ctx['slow'][0], ctx['slow'][1] + 1, step):
                if b >= a or (F(2 * a * b, a + b) * 10).denominator != 1:
                    continue
                for D in range(ctx['D'][0], ctx['D'][1] + 1, step):
                    t1, t2 = F(D, a), F(D, b)
                    if (t1 * 4).denominator == 1 and (t2 * 4).denominator == 1 and \
                            (t1 + t2).denominator == 1 and t1 + t2 <= 9:
                        out.append((a, b, D))
        return out

    @staticmethod
    def params(r):
        key = r.pick(sorted(RoundTripSpeed.CONTEXTS))
        a, b, D = r.pick(RoundTripSpeed.COMBOS[key])
        return dict(who=r.person(), key=key, a=a, b=b, D=D, x=r.pick(RoundTripSpeed.CONTEXTS[key]['X']))

    fallback = dict(who=person('Carmen'), key='drive', a=60, b=40, D=120, x=30)

    @staticmethod
    def solve(p):
        a, b = p['a'], p['b']
        return F(2 * a * b, a + b)

    @staticmethod
    def render(p):
        w, key, a, b, D, x = p['who'], p['key'], p['a'], p['b'], p['D'], p['x']
        if key == 'drive':
            stem = (f"{w} drove {D} miles to visit {w.his} aunt and averaged {a} miles per hour on the way there. "
                    f"Coming home on the same roads, heavy traffic held {w.him} to an average of {b} miles per hour. "
                    f"{w.His} car gets about {x} miles per gallon.")
            t1, t2, out, back = F(D, a), F(D, b), 'There', 'Back'
        elif key == 'bike':
            stem = (f"{w} rode {w.his} bike {D} miles to a lake, mostly uphill, averaging {b} miles per hour. "
                    f"{w.He} rode home the same way, mostly downhill, at {a} miles per hour. {w.He} packed "
                    f"{word(x)} bottles of water for the ride.")
            t1, t2, out, back = F(D, b), F(D, a), 'There (uphill)', 'Back (downhill)'
        else:
            stem = (f"{w} paddled a kayak {D} miles upstream at {b} miles per hour, then turned around and paddled "
                    f"the same {D} miles back downstream at {a} miles per hour. {w.His} kayak is {x} feet long.")
            t1, t2, out, back = F(D, b), F(D, a), 'Upstream', 'Downstream'
        sp1, sp2 = (a, b) if key == 'drive' else (b, a)
        ask = f"What was {w}'s average speed for the whole round trip, in miles per hour?"
        steps = [
            f"{out}: {D} ÷ {sp1} = {plural(t1, 'hour')}. {back}: {D} ÷ {sp2} = {plural(t2, 'hour')}.",
            f"Total: {2 * D} miles in {num(t1)} + {num(t2)} = {plural(t1 + t2, 'hour')}.",
            f"Average speed = total distance ÷ total time = {2 * D} ÷ {num(t1 + t2)} = "
            f"{num(F(2 * D) / (t1 + t2))} miles per hour (not the simple average of the two speeds).",
        ]
        return dict(stem=stem, ask=ask, steps=steps)


RoundTripSpeed.COMBOS = {k: RoundTripSpeed._combos(k) for k in RoundTripSpeed.CONTEXTS}


@template(id='t4.up-then-down.v1', tier=4, topic='percent', kind='pct', seconds=85)
class UpThenDown:
    ITEMS = ['patio umbrella', 'cordless drill', 'snow shovel', 'garden hose', 'tool chest']

    @staticmethod
    def params(r):
        key = r.pick(['store', 'town', 'stock'])
        if key == 'town':
            a, b = r.pick([10, 20, 25]), r.pick([10, 20, 25])
        else:
            a, b = r.pick([10, 20, 25, 30, 40, 50]), r.pick([10, 20, 25, 30, 40, 50])
        f = F(100 + a, 100) * F(100 - b, 100)
        if f == 1:
            raise Retry
        return dict(who=r.person(), key=key, a=a, b=b, up_first=r.chance(0.6), item=r.pick(UpThenDown.ITEMS),
                    x=r.pick([6, 8, 12, 15, 20, 40]))

    fallback = dict(who=person('Raul'), key='store', a=20, b=20, up_first=True, item='cordless drill', x=12)

    @staticmethod
    def solve(p):
        f = F(100 + p['a'], 100) * F(100 - p['b'], 100)
        return abs(1 - f) * 100

    @staticmethod
    def render(p):
        w, key, a, b, item, x = p['who'], p['key'], p['a'], p['b'], p['item'], p['x']
        up_first = p['up_first']
        if key == 'store':
            ch = {'up': f"raised the price of a {item} by {a}%", 'down': f"cut the price of a {item} by {b}%"}
            ch2 = {'up': f"raised that new price by {a}%", 'down': f"put it on sale for {b}% off that new price"}
            first, second = ('up', 'down') if up_first else ('down', 'up')
            stem = (f"In March, the hardware store where {w} works {ch[first]}. In June, the store {ch2[second]}. "
                    f"{w} has worked at the store for {x} months.")
            thing, start, end = 'price', 'the original price', 'the June price'
        elif key == 'town':
            ch = {'up': f"grew by {a}%", 'down': f"shrank by {b}%"}
            first, second = ('up', 'down') if up_first else ('down', 'up')
            stem = (f"{w} is writing a report about {w.his} town. Its population {ch[first]} from 2016 to 2020, "
                    f"then {ch[second]} from 2020 to 2024. The town has {x} public parks.")
            thing, start, end = 'population', 'the 2016 population', 'the 2024 population'
        else:
            ch = {'up': f"rose {a}%", 'down': f"fell {b}%"}
            first, second = ('up', 'down') if up_first else ('down', 'up')
            stem = (f"{w} owns {x} shares of a company's stock. On Monday the share price {ch[first]}. On Tuesday "
                    f"it {ch[second]} from Monday's closing price.")
            thing, start, end = 'price', "the price before Monday's change", "Tuesday's closing price"
        f = F(100 + a, 100) * F(100 - b, 100)
        lower = f < 1
        ask = f"By what percent is {end} {'lower' if lower else 'higher'} than {start}?"
        v1 = F(100 + a) if up_first else F(100 - b)
        if up_first:
            delta = v1 * b / 100
            s2 = f"Then down {b}%: {b}% of {num(v1)} is {num(delta)}, so {num(v1)} → {num(v1 - delta)}."
            v2 = v1 - delta
            s1 = f"Up {a}%: 100 → {num(v1)}."
        else:
            delta = v1 * a / 100
            s2 = f"Then up {a}%: {a}% of {num(v1)} is {num(delta)}, so {num(v1)} → {num(v1 + delta)}."
            v2 = v1 + delta
            s1 = f"Down {b}%: 100 → {num(v1)}."
        steps = [
            f"Start with a {thing} of 100 (any starting value works the same way).",
            s1,
            s2,
            f"{num(v2)} is {num(abs(100 - v2))} {'below' if lower else 'above'} 100, so it is "
            f"{pct(abs(100 - v2))} {'lower' if lower else 'higher'}.",
        ]
        return dict(stem=stem, ask=ask, steps=steps)


@template(id='t4.combined-average.v1', tier=4, topic='averages', kind='dec', unit='points', seconds=85)
class CombinedAverage:
    CONTEXTS = {
        'test': dict(unit='points', who='students', m=(62, 94), X=[20, 25, 30, 40],
                     stem="{w} teaches two sections of algebra. On Friday's test, the {n1} students in {his} "
                          "first-period class averaged {m1} points, and the {n2} students in {his} fourth-period "
                          "class averaged {m2} points. The test had {x} questions.",
                     ask="What was the average score for all of the students in both classes together, in points?"),
        'boxes': dict(unit='boxes', who='workers', m=(40, 90), X=['10 p.m.', '11 p.m.', 'midnight'],
                      stem="At the warehouse where {w} works, the {n1} workers on the day shift packed an average "
                           "of {m1} boxes each on Monday. The {n2} workers on the night shift, which started at "
                           "{x}, packed an average of {m2} boxes each.",
                      ask="What was the average number of boxes packed per worker across both shifts?"),
        'run': dict(unit='minutes', who='runners', m=(22, 40), X=[3, 4, 5],
                    stem="{w}'s running club timed its members in a 5-kilometer race. The {n1} runners in the "
                         "morning group averaged {m1} minutes, and the {n2} runners in the evening group averaged "
                         "{m2} minutes. The course had {x} water stations.",
                    ask="What was the average time for all the runners in both groups, in minutes?"),
    }

    @staticmethod
    def params(r):
        key = r.pick(sorted(CombinedAverage.CONTEXTS))
        ctx = CombinedAverage.CONTEXTS[key]
        N = r.pick([20, 25, 30, 40, 50, 60])  # divide by these without long division
        n1 = r.int(6, N - 6)
        n2 = N - n1
        if abs(n1 - n2) < 4 or max(n1, n2) > 36:
            raise Retry
        m1, m2 = r.int(*ctx['m']), r.int(*ctx['m'])
        if abs(m1 - m2) < 4:
            raise Retry
        avg = F(n1 * m1 + n2 * m2, N)
        if (avg * 2).denominator != 1 or avg == F(m1 + m2, 2):
            raise Retry
        return dict(who=r.person(), key=key, n1=n1, n2=n2, m1=m1, m2=m2, x=r.pick(ctx['X']))

    fallback = dict(who=person('Victor'), key='test', n1=20, n2=30, m1=82, m2=72, x=25)

    @staticmethod
    def solve(p):
        # weighted shortcut: start at m2, move toward m1 by n1/N of the gap
        N = p['n1'] + p['n2']
        return p['m2'] + F(p['n1'], N) * (p['m1'] - p['m2'])

    @staticmethod
    def render(p):
        ctx = CombinedAverage.CONTEXTS[p['key']]
        w, n1, n2, m1, m2 = p['who'], p['n1'], p['n2'], p['m1'], p['m2']
        u = ctx['unit']
        x = word(p['x']) if isinstance(p['x'], int) and p['x'] <= 10 else p['x']
        stem = _fmt(ctx['stem'], w, n1=n1, n2=n2, m1=m1, m2=m2, x=x)
        s1, s2 = n1 * m1, n2 * m2
        N = n1 + n2
        steps = [
            f"First group total: {n1} × {m1} = {num(s1)} {u}.",
            f"Second group total: {n2} × {m2} = {num(s2)} {u}.",
            f"Together: {num(s1)} + {num(s2)} = {num(s1 + s2)} {u} for {n1} + {n2} = {N} {ctx['who']}.",
            f"Average: {num(s1 + s2)} ÷ {N} = {num(F(s1 + s2, N))} {u}.",
        ]
        return dict(stem=stem, ask=ctx['ask'], steps=steps, unit=u)


@template(id='t4.circle-area-ratio.v1', tier=4, topic='geometry', kind='frac', seconds=85)
class CircleAreaRatio:
    PAIRS = {
        'pizza': [(10, 12), (10, 14), (12, 14), (12, 16), (12, 18), (14, 16), (14, 18), (10, 16), (8, 12),
                  (16, 18)],
        'cake': [(6, 8), (6, 9), (8, 10), (8, 12), (9, 12), (6, 10)],
        'rug': [(4, 6), (5, 6), (6, 8), (5, 8), (6, 9), (6, 10), (8, 10)],
    }

    @staticmethod
    def params(r):
        key = r.pick(['pizza', 'cake', 'rug'])
        s, l = r.pick(CircleAreaRatio.PAIRS[key])
        x = {'pizza': r.int(4, 9), 'cake': r.pick([325, 350]), 'rug': r.pick([14, 15, 16, 18])}[key]
        return dict(who=r.person(), key=key, s=s, l=l, x=x)

    fallback = dict(who=person('Eli'), key='pizza', s=12, l=16, x=6)

    @staticmethod
    def solve(p):
        return (F(p['l'], 2) ** 2) / (F(p['s'], 2) ** 2)

    @staticmethod
    def render(p):
        w, key, s, l, x = p['who'], p['key'], p['s'], p['l'], p['x']
        if key == 'pizza':
            stem = (f"{w} is ordering pizza for {word(x)} friends. The pizzeria sells round pizzas in two sizes: "
                    f"{a_an(s)}-inch small and {a_an(l)}-inch large, where the size is the diameter. Both have the same crust "
                    f"and toppings.")
            ask = "The large pizza has how many times the area of the small pizza?"
            u = 'inches'
        elif key == 'cake':
            stem = (f"{w} has a recipe for {a_an(s)}-inch round cake, but {w.he} wants to bake it in {a_an(l)}-inch round "
                    f"pan instead, filled to the same depth. The oven is set to {x} degrees.")
            ask = f"How many times the original recipe should {w} make to fill the bigger pan?"
            u = 'inches'
        else:
            stem = (f"{w}'s living room has a round rug that is {s} feet across. {w.He} wants to replace it with a "
                    f"round rug that is {l} feet across. The room is {x} feet long.")
            ask = "The new rug will cover how many times as much floor area as the old rug?"
            u = 'feet'
        ans = F(l * l, s * s)
        if s % 2 == 0 and l % 2 == 0:
            r1, r2 = s // 2, l // 2
            steps = [
                f"Radii: {r1} and {r2} {u}.",
                f"Areas: π × {r1}² = {r1 * r1}π and π × {r2}² = {r2 * r2}π.",
                f"Ratio: {r2 * r2}π ÷ {r1 * r1}π = {frac(ans)}.",
            ]
        else:
            q = F(l, s)
            steps = [
                "A circle's area is π × radius², so area grows with the square of the diameter.",
                f"Ratio of diameters: {l} ÷ {s} = {frac(q)}.",
                f"Ratio of areas: ({frac(q)})² = {frac(ans)}.",
            ]
        return dict(stem=stem, ask=ask, steps=steps)


@template(id='t4.median-table.v1', tier=4, topic='data', kind='dec', unit='books', seconds=90)
class MedianTable:
    CONTEXTS = {
        'books': dict(col=('Books read', 'Number of students'), unit='books', who='students', top=5,
                      X=[6, 8, 10],
                      stem="{w}'s class kept track of how many books each student read over winter break, and the "
                           "table shows the results. The school library lets each student borrow up to {x} books "
                           "at a time.",
                      ask="What is the median number of books read over the break?"),
        'pets': dict(col=('Number of pets', 'Households'), unit='pets', who='households', top=4, X=[2, 3, 4],
                     stem="{w} asked every household on {his} street how many pets it has and recorded the results "
                          "in the table. It took {him} {x} afternoons to reach everyone.",
                     ask="What is the median number of pets per household?"),
        'goals': dict(col=('Goals scored', 'Number of games'), unit='goals', who='games', top=5,
                      X=[60, 70, 80, 90],
                      stem="{w}'s soccer team kept track of how many goals it scored in each game this season, "
                           "shown in the table. Each game lasted {x} minutes.",
                      ask="What is the median number of goals the team scored per game?"),
    }

    @staticmethod
    def params(r):
        key = r.pick(sorted(MedianTable.CONTEXTS))
        ctx = MedianTable.CONTEXTS[key]
        counts = [r.int(1, 9) for _ in range(ctx['top'] + 1)]
        N = sum(counts)
        if not 15 <= N <= 40:
            raise Retry
        data = sorted(v for v, c in enumerate(counts) for _ in range(c))
        med = F(data[(N - 1) // 2] + data[N // 2], 2)
        mode = max(range(len(counts)), key=lambda v: counts[v])
        if counts.count(max(counts)) > 1 or med == mode or med == F(ctx['top'], 2):
            raise Retry
        x = r.pick(ctx['X'])
        return dict(who=r.person(), key=key, counts=counts, x=word(x) if x <= 10 else x)

    fallback = dict(who=person('Ruth'), key='books', counts=[2, 6, 5, 7, 3, 1], x='eight')

    @staticmethod
    def solve(p):
        data = []
        for v, c in enumerate(p['counts']):
            data += [v] * c
        data.sort()
        n = len(data)
        return F(data[n // 2]) if n % 2 else F(data[n // 2 - 1] + data[n // 2], 2)

    @staticmethod
    def render(p):
        ctx = MedianTable.CONTEXTS[p['key']]
        w, counts, u, who = p['who'], p['counts'], ctx['unit'], ctx['who']
        stem = _fmt(ctx['stem'], w, x=p['x'])
        table = dict(headers=list(ctx['col']), rows=[[v, c] for v, c in enumerate(counts)])
        N = sum(counts)
        cum, run = [], 0
        for v, c in enumerate(counts):
            run += c
            cum.append(run)

        def at(pos):  # value at 1-based position
            return next(v for v, c in enumerate(cum) if c >= pos)
        steps = [f"Total: {' + '.join(str(c) for c in counts)} = {N} {who}."]
        if N % 2:
            m = (N + 1) // 2
            steps.append(f"With {N} values in order, the median is the {ordinal(m)} value.")
        else:
            m = N // 2
            steps.append(f"With {N} values in order, the median is the average of the {ordinal(m)} and "
                         f"{ordinal(m + 1)} values.")
        steps.append("Running totals: " + ', '.join(f"through {v}: {c}" for v, c in enumerate(cum)) + '.')
        if N % 2:
            v = at(m)
            steps.append(f"The {ordinal(m)} value falls in the row for {plural(v, u[:-1], u)}, so the median is {v} {u}.")
        else:
            v1, v2 = at(m), at(m + 1)
            if v1 == v2:
                steps.append(f"Both fall in the row for {plural(v1, u[:-1], u)}, so the median is {v1} {u}.")
            else:
                steps.append(f"They are {v1} and {v2}, so the median is ({v1} + {v2}) ÷ 2 = "
                             f"{num(F(v1 + v2, 2))} {u}.")
        return dict(stem=stem, ask=ctx['ask'], steps=steps, table=table, unit=u)


@template(id='t4.catch-up.v1', tier=4, topic='rates', kind='int', unit='minutes', seconds=95)
class CatchUp:
    CONTEXTS = {
        'bike': dict(v1=(8, 14), v2=(12, 20), d=[10, 15, 20, 30], L=[20, 25, 30]),
        'truck': dict(v1=(40, 55), v2=(50, 70), d=[5, 10, 12, 15, 20], L=[60, 80, 100, 120]),
        'walk': dict(v1=(3, 4), v2=(5, 8), d=[6, 10, 12, 15, 20], L=[5, 6, 8]),
    }

    @staticmethod
    def params(r):
        key = r.pick(sorted(CatchUp.CONTEXTS))
        ctx = CatchUp.CONTEXTS[key]
        v1, v2, d = r.int(*ctx['v1']), r.int(*ctx['v2']), r.pick(ctx['d'])
        if v2 <= v1 or key == 'truck' and (v1 % 5 or v2 % 5):
            raise Retry
        if (v1 * d) % (v2 - v1):
            raise Retry
        t = v1 * d // (v2 - v1)  # minutes after the second person leaves
        L = r.pick(ctx['L'])
        if not 5 <= t <= 120 or 100 % F(v1 * d, 60).denominator or F(v2 * t, 60) >= L:
            raise Retry
        if t in (v1, v2, d, L) and r.chance(0.8):
            raise Retry  # keep the answer from echoing a number in the stem
        ppl = r.people(2) if key != 'truck' else [r.person()]
        return dict(who=ppl, key=key, v1=v1, v2=v2, d=d, L=L)

    fallback = dict(who=[person('Zoe'), person('Hugo')], key='bike', v1=12, v2=18, d=30, L=25)

    @staticmethod
    def solve(p):
        # minute-by-minute: positions in miles * 60
        v1, v2, d = p['v1'], p['v2'], p['d']
        return next(t for t in range(1, 10000) if v2 * t >= v1 * (t + d))

    @staticmethod
    def render(p):
        key, v1, v2, d, L = p['key'], p['v1'], p['v2'], p['d'], p['L']
        if key == 'bike':
            a, b = p['who']
            stem = (f"{a} set out on {a.his} bike along the river trail, riding at a steady {v1} miles per hour. "
                    f"{b} left from the same spot {d} minutes later and followed the same trail at a steady {v2} "
                    f"miles per hour. The trail is {L} miles long.")
            ask = f"How many minutes after starting did {b} catch up to {a}?"
            first, second = a.name, b.name
        elif key == 'walk':
            a, b = p['who']
            stem = (f"{a} started walking along a straight lakeside path at a steady {v1} miles per hour. {b} "
                    f"started running from the same spot {d} minutes later, going the same direction at a steady "
                    f"{v2} miles per hour. The path is {L} miles long.")
            ask = f"How many minutes after starting to run did {b} catch up to {a}?"
            first, second = a.name, b.name
        else:
            w = p['who'][0]
            stem = (f"A moving truck left {w}'s old apartment and headed for {w.his} new place at a steady {v1} "
                    f"miles per hour. {w} left the same apartment {d} minutes later in {w.his} car, following the "
                    f"same route at a steady {v2} miles per hour. The new place is {L} miles away.")
            ask = f"How many minutes after {w} left did {w.he} catch up to the truck?"
            first, second = 'the truck', w.name
        hd = F(d, 60)
        head = v1 * hd
        g = v2 - v1
        th = head / g
        steps = [
            f"Head start: in {d} minutes ({frac(hd)} hour), {first} covers {v1} × {frac(hd)} = "
            f"{plural(head, 'mile')}.",
            f"{cap(second)} gains {v2} − {v1} = {plural(g, 'mile')} per hour.",
            f"Time to close the gap: {num(head)} ÷ {g} = {frac(th)} {'hour' if th <= 1 else 'hours'} = "
            f"{num(th * 60)} minutes.",
        ]
        return dict(stem=stem, ask=ask, steps=steps)
