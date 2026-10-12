"""Tier 1 (Warm-up) and tier 2 (Everyday) templates."""
from fractions import Fraction as F

from engine import (Retry, template, person, usd, usd2, num, frac, mixed, pct, clock, plural, word, cap,
                    a_an)


# ---------------------------------------------------------------- local helpers
def pv(w, **kw):
    """Pronoun/name fields for str.format skins."""
    d = dict(w=w, he=w.he, He=w.He, him=w.him, his=w.his, His=w.His)
    d.update(kw)
    return d


def and_list(items):
    items = [str(x) for x in items]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ', '.join(items[:-1]) + ', and ' + items[-1]


def cup_amt(x):
    x = F(x)
    return f"{mixed(x)} {'cup' if x <= 1 else 'cups'}"


def inch(x):
    x = F(x)
    return f"{mixed(x)} {'inch' if x <= 1 else 'inches'}"


def hours_phrase(h):
    h = F(h)
    return f"{mixed(h)} {'hour' if h <= 1 else 'hours'}"


# =================================================================== TIER 1
@template(id='t1.restaurant-tip.v1', tier=1, topic='money', kind='money', seconds=35)
class RestaurantTip:
    SKINS = [
        "{w} takes {his} parents out for a birthday lunch. The bill comes to {B} before the tip, and {he} "
        "wants to leave a {r}% tip on that amount.",
        "{w} and two coworkers stop at a diner for breakfast, and {w} offers to pay. The check is {B}. "
        "{He} plans to add a {r}% tip on the full check.",
        "After a long hike, {w} stops at a cafe for dinner. {His} bill is {B} before tip. {He} always tips "
        "{r}% of the bill.",
        "{w} orders takeout noodles and dumplings for the family. The order comes to {B}, and {he} adds a "
        "{r}% tip for the delivery driver.",
    ]

    @staticmethod
    def params(r):
        bill = r.int(22, 88) * 100 + r.pick([0, 0, 20, 40, 60, 80])
        return dict(who=r.person(), skin=r.int(0, 3), rate=r.pick([15, 20]), bill=bill, total=r.chance(0.5))

    fallback = dict(who=person('Rosa'), skin=0, rate=15, bill=4860, total=False)

    @staticmethod
    def solve(p):
        tip = F(p['bill'] * p['rate'], 100)
        return tip + (p['bill'] if p['total'] else 0)

    @staticmethod
    def render(p):
        w, b, rate = p['who'], p['bill'], p['rate']
        stem = RestaurantTip.SKINS[p['skin']].format(**pv(w, B=usd(b), r=rate))
        t10 = b // 10
        if rate == 15:
            tip = t10 + t10 // 2
            steps = [f"10% of {usd(b)} is {usd(t10)}.",
                     f"5% is half of that: {usd(t10 // 2)}.",
                     f"15% tip: {usd(t10)} + {usd(t10 // 2)} = {usd(tip)}."]
        else:
            tip = 2 * t10
            steps = [f"10% of {usd(b)} is {usd(t10)}.",
                     f"20% is twice that: 2 × {usd(t10)} = {usd(tip)}."]
        if p['total']:
            steps.append(f"Total: {usd(b)} + {usd(tip)} = {usd(b + tip)}.")
            ask = f"How much does {w} pay in all, including the tip?"
        else:
            ask = "How much is the tip?"
        return dict(stem=stem, ask=ask, steps=steps)


@template(id='t1.making-change.v1', tier=1, topic='money', kind='money', seconds=40)
class MakingChange:
    SKINS = [
        ("{w} stops at the hardware store for a weekend project.",
         [('a box of screws', [349, 425, 275, 395]), ('a roll of tape', [489, 525, 450]),
          ('a paintbrush', [650, 575, 725])]),
        ("{w} shops at the farmers market on Saturday morning.",
         [('a jar of honey', [650, 725, 800]), ('a loaf of sourdough', [575, 625, 550]),
          ('a pint of blueberries', [450, 399, 425])]),
        ("{w} picks up school supplies before classes start.",
         [('a binder', [349, 425, 299]), ('a pack of pens', [275, 325, 199]),
          ('a calculator', [895, 1050, 975])]),
        ("{w} runs to the pet store for {his} dog.",
         [('a bag of treats', [499, 575, 625]), ('a chew toy', [350, 425, 399]),
          ('a new leash', [1200, 1150, 1375])]),
    ]

    @staticmethod
    def params(r):
        skin = r.int(0, len(MakingChange.SKINS) - 1)
        prices = [r.pick(ps) for _, ps in MakingChange.SKINS[skin][1]]
        tot = sum(prices)
        paid = 2000 if tot < 2000 else 5000
        if tot < 2000 and r.chance(0.25):
            paid = 5000
        return dict(who=r.person(), skin=skin, prices=prices, paid=paid)

    fallback = dict(who=person('Luis'), skin=0, prices=[349, 489, 650], paid=2000)

    @staticmethod
    def solve(p):
        # count up from the total to the bill, cent by cent in dollars-and-cents pieces
        return p['paid'] - sum(p['prices'])

    @staticmethod
    def render(p):
        w = p['who']
        intro, items = MakingChange.SKINS[p['skin']]
        names = [n for n, _ in items]
        pr = p['prices']
        bought = and_list([f"{n} for {usd(c)}" for n, c in zip(names, pr)])
        stem = (intro.format(**pv(w)) + f" {w.He} buys {bought}. There's no sales tax, and {w.he} pays with "
                f"a {usd(p['paid'])} bill.")
        tot = sum(pr)
        steps = [f"Total: {usd(pr[0])} + {usd(pr[1])} + {usd(pr[2])} = {usd(tot)}.",
                 f"Change: {usd(p['paid'])} − {usd(tot)} = {usd(p['paid'] - tot)}."]
        return dict(stem=stem, ask=f"How much change should {w} get back?", steps=steps)


@template(id='t1.elapsed-minutes.v1', tier=1, topic='time', kind='int', unit='minutes', seconds=35)
class ElapsedMinutes:
    # (stem, ask, earliest start, latest start, min length, max length)
    SKINS = [
        ("{w}'s movie started at {s}, and the credits began rolling at {e} as {he} headed for the "
         "exit.", "How many minutes long was the movie, from start to credits?", 13 * 60, 20 * 60, 90, 160),
        ("At {s}, {w} put a loaf of bread in the oven. {He} took it out at {e}, when the crust was golden "
         "brown.", "For how many minutes did the bread bake?", 9 * 60, 17 * 60, 30, 75),
        ("{w} left home at {s} to drive to a lake cabin. {He} made no stops, and the dashboard clock read {e} "
         "when {he} pulled into the cabin's driveway.", "How many minutes did the drive take?", 7 * 60, 10 * 60,
         60, 200),
        ("At {s}, {w} started a volunteer shift at the library. The shift ended at {e}, and {he} walked "
         "home.", "How many minutes long was the shift?", 8 * 60, 14 * 60, 90, 240),
    ]

    @staticmethod
    def params(r):
        skin = r.int(0, 3)
        _, _, lo, hi, mn, mx = ElapsedMinutes.SKINS[skin]
        s = r.int(lo // 5, hi // 5) * 5
        e = s + r.int(mn // 5, mx // 5) * 5
        if s % 60 == 0 or e % 60 == 0 or s // 60 == e // 60:
            raise Retry
        return dict(who=r.person(), skin=skin, s=s, e=e)

    fallback = dict(who=person('Grace'), skin=0, s=19 * 60 + 40, e=21 * 60 + 15)

    @staticmethod
    def solve(p):
        return p['e'] - p['s']

    @staticmethod
    def render(p):
        w, s, e = p['who'], p['s'], p['e']
        stem, ask = ElapsedMinutes.SKINS[p['skin']][:2]
        stem = stem.format(**pv(w, s=clock(s), e=clock(e)))
        h1 = (s // 60 + 1) * 60
        h2 = (e // 60) * 60
        a, c = h1 - s, e - h2
        steps = [f"From {clock(s)} to {clock(h1)} is {a} minutes."]
        parts = [a]
        if h2 > h1:
            k = (h2 - h1) // 60
            steps.append(f"From {clock(h1)} to {clock(h2)} is {plural(k, 'hour')}, or {k * 60} minutes.")
            parts.append(k * 60)
        steps.append(f"From {clock(h2)} to {clock(e)} is {c} minutes.")
        parts.append(c)
        steps.append(f"Total: {' + '.join(map(str, parts))} = {sum(parts)} minutes.")
        return dict(stem=stem, ask=ask, steps=steps)


@template(id='t1.unit-price-scale.v1', tier=1, topic='rates', kind='money', seconds=40)
class UnitPriceScale:
    # (stem, ask, unit, units, unit prices in cents)
    SKINS = [
        ("A farm stand sells a {q1}-pound bag of apples for {P}. {w} wants {q2} pounds for pies, and the stand "
         "will weigh out any amount at the same price per pound.", "How much will {q2} pounds of apples cost?",
         'pound', 'pounds', [125, 150, 175, 200, 225, 250, 275]),
        ("At the hardware store, {q1} feet of rope costs {P}. {w} needs {q2} feet to hang a porch swing, and "
         "the store cuts rope to any length at the same price per foot.", "How much will {q2} feet of rope cost?",
         'foot', 'feet', [35, 40, 45, 60, 75, 80, 90]),
        ("{w} is sewing curtains. The fabric {he} likes costs {P} for {q1} yards, and the shop sells it by the "
         "yard at that same rate. {He} needs {q2} yards.", "How much will the fabric cost?",
         'yard', 'yards', [450, 550, 600, 650, 750, 800, 900]),
        ("The bulk bin at the grocery store charges {P} for {q1} pounds of trail mix. {w} wants {q2} pounds "
         "for a camping trip.", "At the same price per pound, how much will {q2} pounds cost?",
         'pound', 'pounds', [350, 425, 450, 500, 550, 600]),
    ]

    @staticmethod
    def params(r):
        skin = r.int(0, 3)
        u = r.pick(UnitPriceScale.SKINS[skin][4])
        q1, q2 = r.int(2, 6), r.int(2, 12)
        if q1 == q2:
            raise Retry
        return dict(who=r.person(), skin=skin, u=u, q1=q1, q2=q2)

    fallback = dict(who=person('Maya'), skin=0, u=150, q1=4, q2=7)

    @staticmethod
    def solve(p):
        total = p['u'] * p['q1']
        return F(total, p['q1']) * p['q2']

    @staticmethod
    def render(p):
        w, q1, q2, u = p['who'], p['q1'], p['q2'], p['u']
        stem, ask, one, many = UnitPriceScale.SKINS[p['skin']][:4]
        P = u * q1
        fmt = pv(w, P=usd(P), q1=q1, q2=q2)
        steps = [f"Price per {one}: {usd(P)} ÷ {q1} = {usd(u)}.",
                 f"{q2} {many}: {q2} × {usd(u)} = {usd(q2 * u)}."]
        return dict(stem=stem.format(**fmt), ask=ask.format(**fmt), steps=steps)


@template(id='t1.split-bill.v1', tier=1, topic='money', kind='money', seconds=40)
class SplitBill:
    # (stem, A range in dollars, A step, B range in cents, B step)
    SKINS = [
        ("{w} and {k} friends order pizza for game night. The pizzas come to {A}, and drinks and dessert add "
         "{B} more. They agree to split the total evenly.", (30, 60), 1, (800, 2000), 50),
        ("{w} and {k} friends rent a lake cabin for a weekend. The rental costs {A}, plus a {B} cleaning "
         "fee. They split the whole cost evenly.", (300, 600), 10, (5000, 15000), 500),
        ("{w} and {k} coworkers chip in for a retirement gift: a gift card worth {A} and a cake that costs "
         "{B}. They split the cost evenly.", (50, 150), 5, (2000, 4500), 100),
        ("{w} and {k} friends go bowling. The lanes cost {A} for the night, and shoe rentals add {B}. They "
         "split the total evenly.", (40, 90), 2, (1000, 2500), 50),
    ]

    @staticmethod
    def params(r):
        skin = r.int(0, 3)
        _, (alo, ahi), astep, (blo, bhi), bstep = SplitBill.SKINS[skin]
        A = r.int(alo // astep, ahi // astep) * astep * 100
        B = r.int(blo // bstep, bhi // bstep) * bstep
        n = r.int(3, 6)
        if (A + B) % n or ((A + B) // n) % 5:
            raise Retry
        return dict(who=r.person(), skin=skin, A=A, B=B, n=n)

    fallback = dict(who=person('Omar'), skin=0, A=4200, B=1200, n=4)

    @staticmethod
    def solve(p):
        return F(p['A'] + p['B'], p['n'])

    @staticmethod
    def render(p):
        w, A, B, n = p['who'], p['A'], p['B'], p['n']
        stem = SplitBill.SKINS[p['skin']][0].format(**pv(w, k=word(n - 1), A=usd(A), B=usd(B)))
        T = A + B
        steps = [f"Total: {usd(A)} + {usd(B)} = {usd(T)}.",
                 f"{w} plus {word(n - 1)} others makes {n} people.",
                 f"Each pays {usd(T)} ÷ {n} = {usd(T // n)}."]
        return dict(stem=stem, ask="How much does each person pay?", steps=steps)


@template(id='t1.garden-fence.v1', tier=1, topic='geometry', kind='int', unit='feet', seconds=35)
class GardenFence:
    SKINS = [
        "{w} is planting a rectangular vegetable garden that measures {L} feet by {W} feet. {He} wants a short "
        "fence around it to keep rabbits out.",
        "{w} is building a rectangular dog run in {his} backyard. It will be {L} feet long and {W} feet wide.",
        "{w} is fencing in a rectangular play area for {his} kids. The area is {L} feet long and {W} feet wide.",
        "{w} is building a rectangular pen for {his} chickens that measures {L} feet by {W} feet.",
    ]
    WALLS = ['garage', 'house', 'barn', 'shed']

    @staticmethod
    def params(r):
        L = r.int(8, 30)
        W = r.int(5, L - 2)
        return dict(who=r.person(), skin=r.int(0, 3), L=L, W=W, three=r.chance(0.4), wall=r.pick(GardenFence.WALLS))

    fallback = dict(who=person('Theo'), skin=0, L=18, W=12, three=False, wall='garage')

    @staticmethod
    def solve(p):
        sides = [p['L'], p['W'], p['L'], p['W']]
        if p['three']:
            sides.remove(p['L'])
        return sum(sides)

    @staticmethod
    def render(p):
        w, L, W = p['who'], p['L'], p['W']
        stem = GardenFence.SKINS[p['skin']].format(**pv(w, L=L, W=W))
        if p['three']:
            stem += f" One {L}-foot side runs along the {p['wall']} wall, so it needs no fence."
            steps = [f"Fence the other {L}-foot side and both {W}-foot sides.",
                     f"{L} + {W} + {W} = {L + 2 * W} feet."]
        else:
            stem += f" {w.He}'ll fence all four sides."
            steps = [f"One length plus one width: {L} + {W} = {L + W} feet.",
                     f"Going all the way around doubles that: 2 × {L + W} = {2 * (L + W)} feet."]
        return dict(stem=stem, ask=f"How many feet of fencing does {w} need?", steps=steps)


@template(id='t1.floor-tiles.v1', tier=1, topic='geometry', kind='int', unit='tiles', seconds=40)
class FloorTiles:
    # (stem, unit noun plural, allowed sizes in inches)
    SKINS = [
        ("{w} is tiling {his} kitchen floor, a rectangle {L} feet long and {W} feet wide. {He} is using square "
         "tiles that measure {s} inches on each side, and they fit exactly with no cutting.", 'tiles', [12, 24]),
        ("{w} is laying square pavers for a backyard patio. The patio will be a rectangle {L} feet by {W} feet, "
         "and each paver is {s} inches on a side. The pavers fit exactly, with no cutting.", 'pavers', [12, 24]),
        ("{w} is covering a playroom floor with square foam mats that are {s} inches on each side. The "
         "room is a rectangle {L} feet long and {W} feet wide, and the mats fit exactly.", 'mats', [24]),
        ("{w} is tiling a small laundry room floor that measures {L} feet by {W} feet. {He} picked square "
         "tiles that are {s} inches on each side, and they fit exactly with no cutting.", 'tiles', [6, 12]),
    ]

    @staticmethod
    def params(r):
        skin = r.int(0, 3)
        s = r.pick(FloorTiles.SKINS[skin][2])
        if skin == 3:
            L, W = r.int(4, 9), r.int(3, 8)
        elif s == 24:
            L, W = 2 * r.int(4, 10), 2 * r.int(3, 9)
        elif s == 12:
            L, W = r.int(6, 14), r.int(5, 12)
        else:
            L, W = r.int(4, 9), r.int(3, 8)
        if W >= L:
            raise Retry
        return dict(who=r.person(), skin=skin, s=s, L=L, W=W)

    fallback = dict(who=person('Kenji'), skin=0, s=24, L=12, W=10)

    @staticmethod
    def solve(p):
        return F(p['L'] * 12, p['s']) * F(p['W'] * 12, p['s'])

    @staticmethod
    def render(p):
        w, s, L, W = p['who'], p['s'], p['L'], p['W']
        stem, noun, _ = FloorTiles.SKINS[p['skin']]
        stem = stem.format(**pv(w, s=s, L=L, W=W))
        one = noun[:-1]
        if s == 12:
            steps = [f"12 inches is 1 foot, so each {one} covers 1 square foot.",
                     f"Area: {L} × {W} = {L * W} square feet, so {L * W} {noun}."]
        elif s == 24:
            a, b = L // 2, W // 2
            steps = [f"24 inches is 2 feet. Along the length: {L} ÷ 2 = {a} {noun}.",
                     f"Along the width: {W} ÷ 2 = {b} {noun}.",
                     f"Total: {a} × {b} = {a * b} {noun}."]
        else:
            a, b = 2 * L, 2 * W
            steps = [f"6 inches is half a foot, so 2 {noun} fit in each foot.",
                     f"Along the length: {L} × 2 = {a}. Along the width: {W} × 2 = {b}.",
                     f"Total: {a} × {b} = {a * b} {noun}."]
        return dict(stem=stem, ask=f"How many {noun} does {w} need?", steps=steps, unit=noun)


@template(id='t1.sale-price.v1', tier=1, topic='percent', kind='money', seconds=35)
class SalePrice:
    ITEMS = [('winter jacket', 40, 160), ('rolling suitcase', 60, 200), ('desk lamp', 20, 80),
             ('pair of hiking boots', 60, 180), ('board game', 20, 60), ('rain jacket', 30, 120)]
    SKINS = [
        "{w} has been waiting for a sale on a {item} that normally costs {P}. This weekend the store has it "
        "marked {d}% off.",
        "The store is taking {d}% off everything this week, including the {item} {w} has had {his} eye on. "
        "Its regular price is {P}.",
        "{w} spots a {item} with a price tag of {P}. A sign on the rack says the price will be {d}% off at "
        "the register.",
    ]

    @staticmethod
    def params(r):
        item, lo, hi = r.pick(SalePrice.ITEMS)
        d = r.pick([10, 20, 25, 30, 40, 50])
        P = r.int(lo, hi)
        if (P * d) % 50:
            raise Retry
        return dict(who=r.person(), skin=r.int(0, 2), item=item, d=d, P=P * 100)

    fallback = dict(who=person('Hana'), skin=0, item='winter jacket', d=25, P=8400)

    @staticmethod
    def solve(p):
        return p['P'] * F(100 - p['d'], 100)

    @staticmethod
    def render(p):
        w, P, d = p['who'], p['P'], p['d']
        stem = SalePrice.SKINS[p['skin']].format(**pv(w, item=p['item'], P=usd(P), d=d))
        X = P * d // 100
        if d == 25:
            steps = [f"25% is one quarter: {usd(P)} ÷ 4 = {usd(X)}."]
        elif d == 50:
            steps = [f"50% is one half: {usd(P)} ÷ 2 = {usd(X)}."]
        elif d == 10:
            steps = [f"10% of {usd(P)} is {usd(X)}."]
        else:
            t = P // 10
            steps = [f"10% of {usd(P)} is {usd(t)}.", f"So {d}% is {d // 10} × {usd(t)} = {usd(X)}."]
        steps.append(f"Sale price: {usd(P)} − {usd(X)} = {usd(P - X)}.")
        return dict(stem=stem, ask=f"What is the sale price of the {p['item']}, before tax?", steps=steps)


@template(id='t1.sales-tax.v1', tier=1, topic='percent', kind='money', seconds=40)
class SalesTax:
    ITEMS = [('bike helmet', 25, 60), ('blender', 30, 90), ('pair of headphones', 20, 80),
             ('garden hose', 18, 45), ('set of mixing bowls', 15, 40), ('toaster', 20, 60)]
    SKINS = [
        "{w} is shopping for a new {item} and finds one priced at {P}. The sales tax where {he} lives is {r}%, "
        "added at the register.",
        "{w} orders a {item} that costs {P} before tax. {His} state charges {ar}% sales tax on the purchase.",
        "A {item} at the local store is marked {P}. {w} decides to buy it, and {r}% sales tax is added at "
        "checkout.",
    ]

    @staticmethod
    def params(r):
        item, lo, hi = r.pick(SalesTax.ITEMS)
        return dict(who=r.person(), skin=r.int(0, 2), item=item, P=r.int(lo, hi) * 100, rate=r.pick([5, 6, 7, 8]))

    fallback = dict(who=person('Felix'), skin=0, item='bike helmet', P=3500, rate=6)

    @staticmethod
    def solve(p):
        return p['P'] * F(100 + p['rate'], 100)

    @staticmethod
    def render(p):
        w, P, rt = p['who'], p['P'], p['rate']
        stem = SalesTax.SKINS[p['skin']].format(**pv(w, item=p['item'], P=usd(P), r=rt, ar=a_an(rt)))
        tax = P * rt // 100
        if rt == 5:
            steps = [f"10% of {usd(P)} is {usd(P // 10)}, so 5% is half of that: {usd(tax)}."]
        else:
            steps = [f"1% of {usd(P)} is {usd(P // 100)}, so {rt}% is {rt} × {usd(P // 100)} = {usd(tax)}."]
        steps.append(f"Total: {usd(P)} + {usd(tax)} = {usd(P + tax)}.")
        return dict(stem=stem, ask=f"What is the total cost of the {p['item']}, including tax?", steps=steps)


@template(id='t1.mean-of-values.v1', tier=1, topic='averages', kind='int', unit='degrees', seconds=40)
class MeanOfValues:
    # (stem, ask, unit, n, mean range, spread, step)
    SKINS = [
        ("{w} keeps a weather log for a science project. The daily high temperatures from Monday to Friday "
         "were {vals} degrees Fahrenheit.", "What was the average daily high for those five days, in degrees?",
         'degrees', 5, (45, 85), 8),
        ("{w} bowled four games at {his} league night on Saturday. {His} scores were {vals}.",
         "What was {w}'s average score for the four games?", None, 4, (110, 175), 20),
        ("{w} is tracking how long {he} practices piano. From Monday to Friday, {he} practiced {vals} "
         "minutes.", "What was {his} average practice time per day, in minutes?", 'minutes', 5, (25, 50), 12),
        ("{w} rode {his} bike to work four days this week. The rides took {vals} minutes.",
         "What was {his} average ride time, in minutes?", 'minutes', 4, (20, 40), 6),
    ]

    @staticmethod
    def params(r):
        skin = r.int(0, 3)
        _, _, _, n, (lo, hi), k = MeanOfValues.SKINS[skin]
        m = r.int(lo, hi)
        dev = [r.int(-k, k) for _ in range(n - 1)]
        last = -sum(dev)
        if abs(last) > k:
            raise Retry
        vals = [m + x for x in dev + [last]]
        if len(set(vals)) < n - 1 or m in vals:
            raise Retry
        return dict(who=r.person(), skin=skin, vals=vals)

    fallback = dict(who=person('Ben'), skin=0, vals=[62, 58, 65, 71, 59])

    @staticmethod
    def solve(p):
        return F(sum(p['vals']), len(p['vals']))

    @staticmethod
    def render(p):
        w, v = p['who'], p['vals']
        stem, ask, unit = MeanOfValues.SKINS[p['skin']][:3]
        fmt = pv(w, vals=and_list(v))
        S = sum(v)
        steps = [f"Sum: {' + '.join(map(str, v))} = {S}.",
                 f"Mean: {S} ÷ {len(v)} = {S // len(v)}."]
        return dict(stem=stem.format(**fmt), ask=ask.format(**fmt), steps=steps, unit=unit)


@template(id='t1.unit-conversion.v1', tier=1, topic='units', kind='dec', unit='feet', seconds=40)
class UnitConversion:
    @staticmethod
    def params(r):
        skin = r.int(0, 3)
        n = r.int(3, 9)
        if skin == 0:
            x = r.pick([15, 18, 20, 24, 30, 36, 42])
            ok = (n * x) % 6 == 0
        elif skin == 1:
            x = r.pick([6, 8, 12, 24, 28])
            ok = (n * x) % 4 == 0
        elif skin == 2:
            x = r.pick([20, 22, 24, 25, 30, 40, 45])
            ok = (n * x) % 15 == 0 and n * x != 60  # avoid a trivial "1 hours"
        else:
            x = r.pick([6, 8, 10, 12])
            ok = True
        if not ok:
            raise Retry
        return dict(who=r.person(), skin=skin, n=n, x=x)

    fallback = dict(who=person('Zoe'), skin=0, n=6, x=18)

    # (stem, ask, small unit, per-big, big unit)
    SKINS = [
        ("{w} is wrapping {n} gifts for a holiday party. Each gift needs a piece of ribbon {x} inches long.",
         "How many feet of ribbon does {w} need in all?", 'inches', 12, 'feet'),
        ("{w} buys {n} cans of tomatoes for a big pot of chili. Each can holds {x} ounces, and there are 16 "
         "ounces in a pound.", "How many pounds of tomatoes is that in all?", 'ounces', 16, 'pounds'),
        ("{w} spends a rainy Saturday watching a baking show. {He} watches {n} episodes, and each one is {x} "
         "minutes long.", "How many hours of the show does {w} watch?", 'minutes', 60, 'hours'),
        ("{w} is running a lemonade stand. {He} makes {n} pitchers of lemonade, and each pitcher holds {x} cups. "
         "There are 4 cups in a quart.", "How many quarts of lemonade does {w} make?", 'cups', 4, 'quarts'),
    ]

    @staticmethod
    def solve(p):
        per = {0: 12, 1: 16, 2: 60, 3: 4}[p['skin']]
        return F(p['n'], per) * p['x']

    @staticmethod
    def render(p):
        w, n, x = p['who'], p['n'], p['x']
        stem, ask, small, per, big = UnitConversion.SKINS[p['skin']]
        fmt = pv(w, n=word(n), x=x)
        T = n * x
        steps = [f"Total: {n} × {x} = {T} {small}.",
                 f"There are {per} {small} in each of the {big}: {T} ÷ {per} = {num(F(T, per))} {big}."]
        if p['skin'] == 0:
            steps[1] = f"There are 12 inches in a foot: {T} ÷ 12 = {num(F(T, 12))} feet."
        elif p['skin'] == 1:
            steps[1] = f"There are 16 ounces in a pound: {T} ÷ 16 = {num(F(T, 16))} pounds."
        elif p['skin'] == 2:
            steps[1] = f"There are 60 minutes in an hour: {T} ÷ 60 = {num(F(T, 60))} hours."
        else:
            steps[1] = f"There are 4 cups in a quart: {T} ÷ 4 = {num(F(T, 4))} quarts."
        return dict(stem=stem.format(**fmt), ask=ask.format(**fmt), steps=steps, unit=big)


@template(id='t1.days-to-goal.v1', tier=1, topic='rates', kind='int', unit='weeks', seconds=40)
class DaysToGoal:
    GOALS = ['new bike', 'pair of concert tickets', 'tablet', 'used guitar', 'camping tent']

    @staticmethod
    def params(r):
        skin = r.int(0, 2)
        k = r.int(3, 14)
        if skin == 0:
            rate = r.pick([5, 6, 8, 10, 15, 20, 25])
            have = r.int(2, 16) * 5
            goal = have + k * rate
            if goal % 5 or goal > 400:
                raise Retry
        elif skin == 1:
            rate = r.pick([15, 20, 25, 30, 40])
            goal = r.int(18, 48) * 10
            have = goal - k * rate
            if have < 20 or have % 5:
                raise Retry
        else:
            rate = r.pick([25, 40, 50, 75])
            goal = r.pick([500, 750, 1000])
            have = goal - k * rate
            if have < 50 or have % 25:
                raise Retry
        return dict(who=r.person(), skin=skin, k=k, rate=rate, goal=goal, have=have, item=r.pick(DaysToGoal.GOALS))

    fallback = dict(who=person('Ruth'), skin=1, k=9, rate=30, goal=350, have=80, item='new bike')

    @staticmethod
    def solve(p):
        # count up period by period
        n, amt = 0, p['have']
        while amt < p['goal']:
            amt += p['rate']
            n += 1
        return n

    @staticmethod
    def render(p):
        w, rate, goal, have = p['who'], p['rate'], p['goal'], p['have']
        left = goal - have
        if p['skin'] == 0:
            stem = (f"{w} is saving for a {p['item']} that costs {usd(goal * 100)}. {w.He} already has "
                    f"{usd(have * 100)} saved and puts away {usd(rate * 100)} each week.")
            ask = f"How many more weeks will it take {w} to have exactly enough?"
            unit, a, b = 'weeks', usd(left * 100), usd(rate * 100)
            first = f"Still needed: {usd(goal * 100)} − {usd(have * 100)} = {a}."
        elif p['skin'] == 1:
            stem = (f"{w} is reading a {goal}-page novel for {w.his} book club and has already read {have} "
                    f"pages. {w.He} plans to read {rate} pages each day until {w.he} finishes.")
            ask = "How many more days will it take to finish the book?"
            unit, a, b = 'days', f"{left} pages", f"{rate}"
            first = f"Pages left: {goal} − {have} = {left}."
        else:
            stem = (f"{w} is working on a {num(goal)}-piece jigsaw puzzle. {w.He} has placed {have} pieces so far "
                    f"and places {rate} more pieces each night.")
            ask = "How many more nights will it take to finish the puzzle?"
            unit, a, b = 'nights', f"{left} pieces", f"{rate}"
            first = f"Pieces left: {num(goal)} − {have} = {left}."
        if p['skin'] == 0:
            last = f"{a} ÷ {b} per week = {left // rate} weeks."
        else:
            last = f"{left} ÷ {rate} = {left // rate} {unit}."
        return dict(stem=stem, ask=ask, steps=[first, last], unit=unit)



# =================================================================== TIER 2
@template(id='t2.stacked-discounts.v1', tier=2, topic='percent', kind='money', seconds=60)
class StackedDiscounts:
    ITEMS = [('winter coat', 80, 240), ('camping tent', 60, 220), ('desk chair', 80, 260),
             ('pair of running shoes', 60, 160), ('stand mixer', 120, 300)]
    SKINS = [
        "{w} has {his} eye on a {item} with a regular price of {P}. This week it's marked {a}% off. At "
        "checkout, {he} also uses a coupon for an extra {b}% off the sale price. {irr}",
        "A store is taking {a}% off every {item}, and {w} finds one with a regular price of {P}. "
        "{He} also has a member coupon that takes {b}% off the already reduced price. {irr}",
        "{w} is shopping for a {item}. The one {he} wants normally sells for {P}, but it's on sale for {a}% off. "
        "The cashier then applies an extra {b}% off the sale price for new members. {irr}",
    ]
    IRR = ["The sale price is good for {x} more days.", "The sale ends in {x} days.",
           "The store is {x} miles from {his} home.", "{He} waited in line for {x} minutes to pay."]

    @staticmethod
    def params(r):
        item, lo, hi = r.pick(StackedDiscounts.ITEMS)
        a = r.pick([20, 25, 30, 40, 50])
        b = r.pick([10, 20, 25])
        P = r.int(lo // 5, hi // 5) * 5
        if (P * a) % 100:
            raise Retry
        S1 = P * (100 - a) // 100
        if (S1 * b) % 100 and (S1 * 100 * b) % 100:
            raise Retry
        return dict(who=r.person(), skin=r.int(0, 2), item=item, a=a, b=b, P=P * 100,
                    irr=r.int(0, 3), x=r.int(3, 12))

    fallback = dict(who=person('Imani'), skin=0, item='winter coat', a=25, b=10, P=12000, irr=1, x=4)

    @staticmethod
    def solve(p):
        return p['P'] * F(100 - p['a'], 100) * F(100 - p['b'], 100)

    @staticmethod
    def render(p):
        w, P, a, b = p['who'], p['P'], p['a'], p['b']
        irr = StackedDiscounts.IRR[p['irr']].format(**pv(w, x=p['x']))
        stem = StackedDiscounts.SKINS[p['skin']].format(**pv(w, item=p['item'], P=usd(P), a=a, b=b, irr=irr))
        X = P * a // 100
        S1 = P - X
        Y = S1 * b // 100
        steps = [f"{a}% of {usd(P)} is {usd(X)}, so the sale price is {usd(P)} − {usd(X)} = {usd(S1)}.",
                 f"The extra {b}% comes off {usd(S1)}, not the original price: {b}% of {usd(S1)} is {usd(Y)}.",
                 f"Final price: {usd(S1)} − {usd(Y)} = {usd(S1 - Y)}."]
        return dict(stem=stem, ask=f"How much does {w} pay for the {p['item']}, before tax?", steps=steps)


@template(id='t2.two-leg-drive.v1', tier=2, topic='rates', kind='int', unit='minutes', seconds=60)
class TwoLegDrive:
    # (stem, speeds1, speeds2, d1 range, d2 range, irrelevant)
    SKINS = [
        ("{w} is driving to {his} grandparents' farm. {He} drives {d1} miles on the highway at a steady "
         "{s1} miles per hour, then {d2} miles on country roads at a steady {s2} miles per hour. {irr}",
         [40, 45, 50, 60], [20, 30, 40], (20, 90), (4, 24),
         ["{His} car's gas tank holds {x} gallons.", "Two cousins are riding along with {him}.",
          "The farm has {x} acres of corn."]),
        ("{w} bikes to work. {He} rides {d1} miles on a bike path at a steady {s1} miles per hour, then {d2} "
         "miles through city streets at a steady {s2} miles per hour. {irr}",
         [10, 12, 15], [6, 8, 10], (3, 12), (2, 5),
         ["{His} bike has {x} gears.", "{His} office is on the {ord} floor.",
          "The bike path has {x} benches along the way."]),
        ("{w} is driving to a ski lodge in the mountains. The first {d1} miles are on the interstate at a steady "
         "{s1} miles per hour. The last {d2} miles are on a winding mountain road, where {he} averages {s2} "
         "miles per hour. {irr}",
         [50, 60], [20, 25, 30], (30, 120), (5, 20),
         ["The lodge has {x} rooms.", "{He} packed {x} pounds of gear.", "The ski lift opens at 9 in the morning."]),
    ]

    @staticmethod
    def params(r):
        skin = r.int(0, 2)
        _, sp1, sp2, (a1, b1), (a2, b2), irrs = TwoLegDrive.SKINS[skin]
        s1, s2 = r.pick(sp1), r.pick(sp2)
        d1, d2 = r.int(a1, b1), r.int(a2, b2)
        m1, m2 = F(d1 * 60, s1), F(d2 * 60, s2)
        if m1.denominator != 1 or m2.denominator != 1 or m1 < 10 or m2 < 5 or m1 % 5 and m2 % 5:
            raise Retry
        if F(d1, s1).denominator not in (1, 2, 3, 4, 5, 6) or F(d2, s2).denominator not in (1, 2, 3, 4, 5, 6):
            raise Retry
        if s1 == s2 or m1 + m2 > 240:
            raise Retry
        return dict(who=r.person(), skin=skin, s1=s1, s2=s2, d1=d1, d2=d2, irr=r.int(0, len(irrs) - 1),
                    x=r.int(12, 21))

    fallback = dict(who=person('Andre'), skin=0, s1=60, s2=30, d1=45, d2=10, irr=0, x=14)

    @staticmethod
    def solve(p):
        # compare against minutes-per-mile for each leg
        return p['d1'] * F(60, p['s1']) + p['d2'] * F(60, p['s2'])

    @staticmethod
    def render(p):
        w = p['who']
        stem, _, _, _, _, irrs = TwoLegDrive.SKINS[p['skin']]
        irr = irrs[p['irr']].format(**pv(w, x=p['x'], ord=['third', 'fourth', 'fifth', 'sixth'][p['x'] % 4]))
        stem = stem.format(**pv(w, d1=p['d1'], d2=p['d2'], s1=p['s1'], s2=p['s2'], irr=irr))
        h1, h2 = F(p['d1'], p['s1']), F(p['d2'], p['s2'])
        m1, m2 = int(h1 * 60), int(h2 * 60)
        steps = [f"First part: {p['d1']} ÷ {p['s1']} = {hours_phrase(h1)}, which is {m1} minutes.",
                 f"Second part: {p['d2']} ÷ {p['s2']} = {hours_phrase(h2)}, which is {m2} minutes.",
                 f"Total: {m1} + {m2} = {m1 + m2} minutes."]
        ask = "How many minutes does the whole trip take?"
        return dict(stem=stem, ask=ask, steps=steps)


@template(id='t2.recipe-scale.v1', tier=2, topic='ratio', kind='frac', unit='cups', seconds=60)
class RecipeScale:
    # (stem, ingredient, base yields, irrelevant)
    SKINS = [
        ("{w}'s pancake recipe makes {o} pancakes and calls for {amt} of flour. {He} is making {n} pancakes "
         "for a family brunch. The recipe says to cook each pancake for 2 minutes per side.", 'flour',
         [8, 10, 12, 16]),
        ("A muffin recipe makes {o} muffins and uses {amt} of sugar. {w} needs {n} muffins for a school bake "
         "sale. The muffins bake at 375 degrees for 20 minutes.", 'sugar', [6, 8, 12, 18]),
        ("{w}'s chili recipe serves {o} people and uses {amt} of chopped onion. {He} is cooking for {n} people "
         "at a neighborhood potluck, and the chili needs to simmer for 45 minutes.", 'chopped onion',
         [4, 6, 8, 12]),
        ("A smoothie recipe makes {o} servings and calls for {amt} of plain yogurt. {w} is making {n} servings "
         "for {his} soccer team after practice. The yogurt was on sale for {usd} a tub.", 'yogurt',
         [2, 4, 6, 8]),
    ]
    AMOUNTS = [F(1, 4), F(1, 3), F(1, 2), F(2, 3), F(3, 4), F(5, 4), F(3, 2)]
    FACTORS = [F(1, 2), F(3, 2), F(5, 2), F(2), F(3), F(3, 4), F(5, 4), F(4, 3), F(2, 3), F(5, 3)]

    @staticmethod
    def params(r):
        skin = r.int(0, 3)
        o = r.pick(RecipeScale.SKINS[skin][2])
        f = r.pick(RecipeScale.FACTORS)
        n = o * f
        if n.denominator != 1 or n < 3 or n > 40:
            raise Retry
        a = r.pick(RecipeScale.AMOUNTS)
        ans = a * f
        if ans.denominator not in (1, 2, 3, 4, 8) or ans > 6 or ans.denominator == 1 and r.chance(0.7):
            raise Retry
        return dict(who=r.person(), skin=skin, o=o, n=int(n), a=a, price=r.pick([250, 300, 350, 400]))

    fallback = dict(who=person('Lucia'), skin=0, o=8, n=20, a=F(3, 4), price=300)

    @staticmethod
    def solve(p):
        # amount per single serving, times the number of servings
        return p['a'] / p['o'] * p['n']

    @staticmethod
    def render(p):
        w, o, n, a = p['who'], p['o'], p['n'], p['a']
        stem, ing, _ = RecipeScale.SKINS[p['skin']]
        stem = stem.format(**pv(w, o=o, n=n, amt=cup_amt(a), usd=usd(p['price'])))
        f = F(n, o)
        ans = a * f
        a_txt = frac(a) if a.denominator == 1 or a < 1 else f"{mixed(a)} = {frac(a)}"
        last = f"{ing.capitalize()}: {frac(a)} × {frac(f)} = {frac(ans)} {'cup' if ans <= 1 else 'cups'}"
        if ans.denominator > 1 and ans > 1:
            last += f", or {mixed(ans)} cups"
        steps = [f"Scale factor: {n} ÷ {o} = {frac(f)}.",
                 f"Original amount: {a_txt} cup{'s' if a > 1 else ''}.",
                 last + "."]
        if a < 1:
            steps.pop(1)
        ask = f"If {w.he} scales the recipe exactly, how many cups of {ing} will {w.he} need?"
        return dict(stem=stem, ask=ask, steps=steps, unit='cup' if ans <= 1 else 'cups')


@template(id='t2.next-score-needed.v1', tier=2, topic='averages', kind='int', unit='points', seconds=60)
class NextScoreNeeded:
    SUBJECTS = ['history', 'biology', 'algebra', 'Spanish', 'chemistry']

    @staticmethod
    def params(r):
        skin = r.int(0, 1)
        n = r.pick([3, 4])
        if skin == 0:
            T = r.pick([80, 82, 85, 88, 90])
            vals = [r.int(T - 14, min(98, T + 10)) for _ in range(n)]
            need = T * (n + 1) - sum(vals)
            if not 75 <= need <= 100:
                raise Retry
        else:
            T = r.pick([140, 150, 160, 170, 180])
            vals = [r.int(T - 30, T + 25) for _ in range(n)]
            need = T * (n + 1) - sum(vals)
            if not 110 <= need <= 240:
                raise Retry
        if need in vals or len(set(vals)) < n:
            raise Retry
        return dict(who=r.person(), skin=skin, T=T, vals=vals, subj=r.pick(NextScoreNeeded.SUBJECTS),
                    x=r.int(22, 34))

    fallback = dict(who=person('Caleb'), skin=0, T=85, vals=[82, 90, 78], subj='history', x=27)

    @staticmethod
    def solve(p):
        # balance method: each score's distance from the target must cancel out
        return p['T'] - sum(v - p['T'] for v in p['vals'])

    @staticmethod
    def render(p):
        w, T, v = p['who'], p['T'], p['vals']
        n = len(v)
        if p['skin'] == 0:
            stem = (f"{w} has taken {word(n)} {p['subj']} tests this term and scored {and_list(v)}. There are "
                    f"{p['x']} students in the class, and one test is left. {w.He} wants {w.his} average on all "
                    f"{word(n + 1)} tests to be exactly {T}.")
            ask = f"What score does {w} need on the last test?"
            unit = 'points'
            what = 'tests'
        else:
            stem = (f"{w} bowls in a league with {p['x'] - 12} teams. So far this season {w.he} has bowled "
                    f"{word(n)} games, scoring {and_list(v)}. {w.He} wants {w.his} average after the next game "
                    f"to be exactly {T}.")
            ask = f"What score does {w} need in the next game?"
            unit = None
            what = 'games'
        X, S = T * (n + 1), sum(v)
        steps = [f"An average of {T} over {n + 1} {what} means a total of {T} × {n + 1} = {num(X)}.",
                 f"Total so far: {' + '.join(map(str, v))} = {num(S)}.",
                 f"Needed: {num(X)} − {num(S)} = {X - S}."]
        return dict(stem=stem, ask=ask, steps=steps, unit=unit)



@template(id='t2.map-scale.v1', tier=2, topic='units', kind='dec', unit='miles', seconds=55)
class MapScale:
    @staticmethod
    def params(r):
        skin = r.int(0, 2)
        if skin == 0:
            k = r.pick([10, 20, 25, 40, 50])
            a, b = F(r.int(5, 18), 4), F(r.int(5, 18), 4)
        elif skin == 1:
            k = r.pick([2, 3, 4])
            a, b = F(r.int(3, 12), 4), F(r.int(3, 12), 4)
        else:
            k = r.pick([F(1, 2), F(2), F(5)])
            a, b = F(r.int(3, 16), 2), F(r.int(3, 16), 2)
        ans = (a + b) * k
        if a == b or (ans * 2).denominator != 1:
            raise Retry
        return dict(who=r.person(), skin=skin, k=k, a=a, b=b, x=r.int(3, 9))

    fallback = dict(who=person('Elena'), skin=0, k=20, a=F(9, 4), b=F(7, 4), x=4)

    @staticmethod
    def solve(p):
        return p['a'] * p['k'] + p['b'] * p['k']

    @staticmethod
    def render(p):
        w, k, a, b, x = p['who'], p['k'], p['a'], p['b'], p['x']
        c = a + b
        if p['skin'] == 0:
            stem = (f"{w} is planning a road trip to the coast with a paper map. On the map, 1 inch represents "
                    f"{k} miles. The route has two straight stretches: the first measures {inch(a)}, and "
                    f"the second measures {inch(b)}. {w.He} plans to leave at {x} in the morning.")
            unit, small = 'miles', 'inches'
            ask = "How many miles long is the route?"
            s1 = f"Map distance: {mixed(a)} + {mixed(b)} = {mixed(c)} inches."
        elif p['skin'] == 1:
            stem = (f"{w} is mapping out a bike ride. On the town's trail map, 1 inch stands for {k} miles. "
                    f"The ride follows the river trail for {inch(a)} on the map, then the park loop for "
                    f"{inch(b)}. The trail map shows {x + 4} drinking fountains.")
            unit, small = 'miles', 'inches'
            ask = "How many miles long is the ride?"
            s1 = f"Map distance: {mixed(a)} + {mixed(b)} = {mixed(c)} inches."
        else:
            kt = 'half a kilometer' if k == F(1, 2) else f"{num(k)} kilometers"
            stem = (f"{w} is planning a hike with a trail map where 1 centimeter represents {kt}. The trail to "
                    f"the waterfall measures {num(a)} centimeters on the map, and the trail back to the parking "
                    f"lot measures {num(b)} centimeters. The parking lot has {x * 10} spaces.")
            unit, small = 'kilometers', 'centimeters'
            ask = "How many kilometers long is the whole hike?"
            s1 = f"Map distance: {num(a)} + {num(b)} = {num(c)} centimeters."
        kk = num(k)
        if small == 'inches':
            last = f"Each inch is {kk} {unit}: {mixed(c)} × {kk} = {num(c * k)} {unit}."
        else:
            last = f"Each centimeter is {kk} {unit}: {num(c)} × {kk} = {num(c * k)} {unit}."
        steps = [s1, last]
        return dict(stem=stem, ask=ask, steps=steps, unit=unit)


@template(id='t2.road-trip-gas.v1', tier=2, topic='money', kind='money', seconds=60)
class RoadTripGas:
    DESTS = ['a lake house', "{his} cousin's wedding", 'a college campus for a tour', 'a state park',
             'a family reunion']
    IRR = ["{His} car's tank holds {t} gallons.", "{He} plans to leave at 7 in the morning.",
           "The drive takes about {h} hours each way, with one stop for lunch."]

    @staticmethod
    def params(r):
        g = r.int(4, 16)
        m = r.pick([20, 24, 25, 30, 32, 35, 40])
        G = r.int(29, 42) * 10
        round_trip = r.chance(0.6)
        D = g * m
        if round_trip and (D % 2 or (D // 2) % 5):
            raise Retry
        if not round_trip and D % 5:
            raise Retry
        return dict(who=r.person(), g=g, m=m, G=G, rt=round_trip, dest=r.pick(RoadTripGas.DESTS),
                    irr=r.int(0, 2), t=r.int(12, 16))

    fallback = dict(who=person('Nadia'), g=12, m=25, G=350, rt=True, dest='a lake house', irr=0, t=14)

    @staticmethod
    def solve(p):
        return F(p['g'] * p['m'], p['m']) * p['G']

    @staticmethod
    def render(p):
        w, g, m, G = p['who'], p['g'], p['m'], p['G']
        D = g * m
        dest = p['dest'].format(**pv(w))
        d = D // 2 if p['rt'] else D
        irr = RoadTripGas.IRR[p['irr']].format(**pv(w, t=p['t'], h=max(2, round(d / 55))))
        if not p['rt']:
            irr = irr.replace(' each way', '')
        if p['rt']:
            stem = (f"{w} is driving to {dest}, which is {d} miles from home, and then driving back. {w.His} car "
                    f"gets {m} miles per gallon, and gas costs {usd2(G)} per gallon. {irr}")
            ask = "How much will gas cost for the round trip?"
            steps = [f"Round trip: 2 × {d} = {D} miles."]
        else:
            stem = (f"{w} is driving {d} miles to {dest}, where {w.he}'ll catch a ride home with family. {w.His} "
                    f"car gets {m} miles per gallon, and gas costs {usd2(G)} per gallon. {irr}")
            ask = "How much will gas cost for the drive?"
            steps = []
        steps += [f"Gas needed: {D} ÷ {m} = {g} gallons.",
                  f"Cost: {g} × {usd2(G)} = {usd(g * G)}."]
        return dict(stem=stem, ask=ask, steps=steps)


@template(id='t2.overtime-pay.v1', tier=2, topic='money', kind='money', seconds=65)
class OvertimePay:
    PLACES = ['warehouse', 'restaurant', 'grocery store', 'bike shop', 'hotel', 'garden center']
    IRR = ["{His} shifts start at 7:00 each morning.", "{He} has worked there for {y} years.",
           "{His} commute is {y} miles each way.", "The {place} has {e} employees."]

    @staticmethod
    def params(r):
        W = r.pick([12, 14, 16, 18, 20, 22, 24])
        shifts = r.chance(0.5)
        if shifts:
            d, h = r.int(4, 6), r.int(8, 12)
            H = d * h
        else:
            d, h = 0, 0
            H = r.int(41, 50)
        if not 41 <= H <= 50:
            raise Retry
        return dict(who=r.person(), W=W, H=H, d=d, h=h, place=r.pick(OvertimePay.PLACES), irr=r.int(0, 3),
                    y=r.int(2, 9), e=r.int(15, 60))

    fallback = dict(who=person('Marcus'), W=18, H=46, d=0, h=0, place='warehouse', irr=1, y=3, e=30)

    @staticmethod
    def solve(p):
        # every hour at the base rate, plus a half-rate bonus on the overtime hours
        return 100 * (p['H'] * p['W'] + (p['H'] - 40) * F(p['W'], 2))

    @staticmethod
    def render(p):
        w, W, H = p['who'], p['W'], p['H']
        irr = OvertimePay.IRR[p['irr']].format(**pv(w, y=p['y'], e=p['e'], place=p['place']))
        worked = (f"worked {word(p['d'])} shifts of {p['h']} hours each" if p['d'] else f"worked {H} hours")
        stem = (f"{w} works at a {p['place']} for {usd(W * 100)} an hour. Any hours over 40 in a week are overtime, "
                f"paid at 1.5 times {w.his} regular rate. {irr} Last week {w.he} {worked}.")
        steps = []
        if p['d']:
            steps.append(f"Hours worked: {p['d']} × {p['h']} = {H}.")
        R, O = 40 * W * 100, W * 150
        X = (H - 40) * O
        steps += [f"Regular pay: 40 × {usd(W * 100)} = {usd(R)}.",
                  f"Overtime rate: 1.5 × {usd(W * 100)} = {usd(O)} an hour, for {H} − 40 = {plural(H - 40, 'hour')}.",
                  f"Overtime pay: {H - 40} × {usd(O)} = {usd(X)}.",
                  f"Total: {usd(R)} + {usd(X)} = {usd(R + X)}."]
        return dict(stem=stem, ask=f"How much did {w} earn last week, before taxes?", steps=steps)


@template(id='t2.coverage-round-up.v1', tier=2, topic='geometry', kind='int', unit='boxes', seconds=60)
class CoverageRoundUp:
    @staticmethod
    def params(r):
        skin = r.int(0, 2)
        if skin == 0:
            c = r.pick([20, 24, 25])
            L, W = r.int(9, 18), r.int(8, 16)
        elif skin == 1:
            c = r.pick([50, 100])
            L, W = r.int(10, 24), r.int(8, 20)
        else:
            c = r.pick([200, 250, 500])
            L, W = r.int(4, 12) * 5, r.int(3, 10) * 5
        A = L * W
        if A % c == 0 or A < 2 * c or W >= L or A // c > 15:
            raise Retry
        return dict(who=r.person(), skin=skin, c=c, L=L, W=W, x=r.int(25, 40),
                    room=r.pick(['bedroom', 'home office', 'den', 'guest room']))

    fallback = dict(who=person('Dev'), skin=0, c=20, L=14, W=12, x=32, room='bedroom')

    @staticmethod
    def solve(p):
        A = p['L'] * p['W']
        return -(-A // p['c'])

    @staticmethod
    def render(p):
        w, c, L, W = p['who'], p['c'], p['L'], p['W']
        if p['skin'] == 0:
            stem = (f"{w} is putting laminate flooring in a rectangular {p['room']} that measures {L} feet by {W} "
                    f"feet. Each box of flooring covers {c} square feet and weighs {p['x']} pounds. The store "
                    f"sells only whole boxes.")
            one, many = 'box', 'boxes'
            ask = f"Ignoring waste, how many boxes does {w} need to buy?"
        elif p['skin'] == 1:
            stem = (f"{w} is sealing a rectangular concrete patio that is {L} feet long and {W} feet wide. One "
                    f"gallon of sealer covers {c} square feet, and it needs {[12, 24, 48][p['x'] % 3]} hours to dry. Sealer is "
                    f"sold only by the whole gallon.")
            one, many = 'gallon', 'gallons'
            ask = f"How many gallons must {w} buy to give the patio one coat?"
        else:
            stem = (f"{w} is reseeding a rectangular lawn that measures {L} feet by {W} feet. A bag of grass seed "
                    f"covers {c} square feet, and the lawn gets about {p['x'] // 5} hours of sun a day. Seed is "
                    f"sold only in whole bags.")
            one, many = 'bag', 'bags'
            ask = f"How many bags of seed must {w} buy to cover the whole lawn?"
        A = L * W
        k = A // c
        steps = [f"Area: {L} × {W} = {num(A)} square feet.",
                 f"{plural(k, one, many)} cover {k} × {c} = {num(k * c)} square feet, which is not enough.",
                 f"{plural(k + 1, one, many)} cover {num((k + 1) * c)} square feet, so {w} needs {k + 1} {many}."]
        return dict(stem=stem, ask=ask, steps=steps, unit=many)


@template(id='t2.latest-start.v1', tier=2, topic='time', kind='int', unit='minutes', seconds=60)
class LatestStart:
    # (task ranges in 5-minute units, target window in minutes after midnight)
    SKINS = [
        ([(4, 6), (9, 12), (2, 3)], (17 * 60, 19 * 60 + 30)),
        ([(2, 3), (5, 9), (1, 2)], (8 * 60, 9 * 60 + 30)),
        ([(6, 8), (9, 12), (3, 4)], (13 * 60, 17 * 60)),
    ]

    @staticmethod
    def params(r):
        skin = r.int(0, 2)
        ranges, (lo, hi) = LatestStart.SKINS[skin]
        tasks = [r.int(a, b) * 5 for a, b in ranges]
        T = r.int(lo // 15, hi // 15) * 15
        s = r.int(1, 9) * 5
        N = T - sum(tasks) - s
        if N % 60 == 0:
            raise Retry
        return dict(who=r.person(), skin=skin, tasks=tasks, T=T, N=N, x=r.int(6, 12))

    fallback = dict(who=person('Leah'), skin=0, tasks=[25, 50, 10], T=18 * 60, N=16 * 60 + 15, x=8)

    @staticmethod
    def solve(p):
        latest = p['T'] - sum(p['tasks'])
        return latest - p['N']

    @staticmethod
    def render(p):
        w, (a, b, c), T, N, x = p['who'], p['tasks'], p['T'], p['N'], p['x']
        if p['skin'] == 0:
            stem = (f"{w} is making lasagna for {x} guests and wants it ready to serve at {clock(T)} sharp. "
                    f"Assembling it takes {a} minutes, baking takes {b} minutes, and it must rest {c} minutes "
                    f"before serving. These steps happen one after another. It is {clock(N)} now.")
            ask = f"At most, how many minutes can {w} wait before starting?"
        elif p['skin'] == 1:
            stem = (f"{w} must be at work by {clock(T)} for a meeting. {w.He} walks {a} minutes to the train "
                    f"station, rides the train for {b} minutes, and then walks {c} minutes to the office. A train "
                    f"ticket costs {usd(225 + 25 * (x % 4))}, and a train leaves the moment {w.he} reaches the "
                    f"platform. It is {clock(N)} now.")
            ask = f"At most, how many minutes can {w} wait before leaving home?"
        else:
            stem = (f"{w} is baking a cake for a birthday party, and it must be frosted by {clock(T)} when "
                    f"the guests arrive. Baking takes {a} minutes, cooling takes {b} minutes, and frosting takes "
                    f"{c} minutes, one after another. The cake will feed {x + 6} people. It is {clock(N)} now.")
            ask = f"At most, how many minutes can {w} wait before starting?"
        t = a + b + c
        D = T - N
        steps = [f"Time needed: {a} + {b} + {c} = {t} minutes.",
                 f"From {clock(N)} to {clock(T)} is {D} minutes.",
                 f"{w} can wait {D} − {t} = {D - t} minutes."]
        return dict(stem=stem, ask=ask, steps=steps)


@template(id='t2.price-list-order.v1', tier=2, topic='data', kind='money', seconds=60)
class PriceListOrder:
    # (intro, irrelevant, items: (name, plural, prices))
    SKINS = [
        ("{w} is picking up breakfast for {his} study group at a coffee shop. The prices, which include tax, are "
         "in the table. The shop opens at 6:30 every morning.",
         [('Drip coffee', 'drip coffees', [200, 225, 250]), ('Latte', 'lattes', [375, 400, 425]),
          ('Hot chocolate', 'hot chocolates', [275, 300]), ('Blueberry muffin', 'blueberry muffins', [250, 275, 300]),
          ('Bagel', 'bagels', [150, 175, 200])]),
        ("{w} is buying snacks for {his} family at a baseball game. The snack bar's prices, tax included, are in "
         "the table. Their seats are in row 14.",
         [('Hot dog', 'hot dogs', [350, 400, 450]), ('Pretzel', 'pretzels', [425, 375]),
          ('Popcorn', 'bags of popcorn', [500, 550]), ('Lemonade', 'lemonades', [300, 325]),
          ('Bottled water', 'bottles of water', [200, 225])]),
        ("{w} is stocking up at a garden center for {his} spring planting. The prices, with tax included, are in "
         "the table. The garden center is 3 miles from {his} house.",
         [('Tomato plant', 'tomato plants', [350, 400]), ('Bag of potting soil', 'bags of potting soil', [625, 650]),
          ('Flower pot', 'flower pots', [475, 550]), ('Seed packet', 'seed packets', [120, 150, 180]),
          ('Watering can', 'watering cans', [899, 1050])]),
    ]

    @staticmethod
    def params(r):
        skin = r.int(0, 2)
        items = PriceListOrder.SKINS[skin][1]
        prices = [r.pick(ps) for _, _, ps in items]
        nrows = r.pick([4, 5])
        rows = sorted(r.sample(range(5), nrows))
        order = r.sample(rows, 3)
        qty = [r.int(1, 4) for _ in order]
        if max(qty) < 2 or len(set(qty)) == 1:
            raise Retry
        return dict(who=r.person(), skin=skin, prices=prices, rows=rows, order=order, qty=qty)

    fallback = dict(who=person('Ezra'), skin=0, prices=[225, 400, 300, 275, 175], rows=[0, 1, 2, 3, 4],
                    order=[1, 3, 4], qty=[3, 2, 1])

    @staticmethod
    def solve(p):
        cart = []
        for i, q in zip(p['order'], p['qty']):
            cart += [p['prices'][i]] * q
        return sum(cart)

    @staticmethod
    def render(p):
        w = p['who']
        intro, items = PriceListOrder.SKINS[p['skin']]
        pr = p['prices']
        table = dict(headers=['Item', 'Price'], rows=[[items[i][0], usd2(pr[i])] for i in p['rows']])
        sing = {'Popcorn': 'bag of popcorn', 'Bottled water': 'bottle of water'}
        bits = [f"{word(q)} {items[i][1] if q > 1 else sing.get(items[i][0], items[i][0].lower())}"
                for i, q in zip(p['order'], p['qty'])]
        stem = intro.format(**pv(w)) + f" {w} orders {and_list(bits)}."
        steps, parts = [], []
        for i, q in zip(p['order'], p['qty']):
            steps.append(f"{items[i][0]}: {q} × {usd(pr[i])} = {usd(q * pr[i])}.")
            parts.append(q * pr[i])
        steps.append(f"Total: {' + '.join(usd(x) for x in parts)} = {usd(sum(parts))}.")
        return dict(stem=stem, ask=f"What is the total cost of {w}'s order?", steps=steps, table=table)


@template(id='t2.currency-exchange.v1', tier=2, topic='units', kind='money', seconds=60)
class CurrencyExchange:
    @staticmethod
    def params(r):
        skin = r.int(0, 2)
        if skin == 0:
            p1, p2 = r.int(10, 80) * 10, r.int(10, 60) * 10
            ok = (p1 + p2) % 20 in (0, 10)
            rate = 20
        elif skin == 1:
            p1, p2 = r.int(16, 30) * 50, r.int(4, 12) * 50
            ok = (p1 + p2) % 150 == 0  # whole dollars, so the division by 150 checks cleanly
            rate = 150
        else:
            rate = r.pick([F(11, 10), F(6, 5)])
            p1, p2 = r.int(12, 60), r.int(8, 40)
            ok = (p1 + p2) % 5 == 0
        if not ok or p1 == p2:
            raise Retry
        items = {0: [('a woven blanket', 'a pair of sandals'), ('a painted bowl', 'a straw hat')],
                 1: [('a souvenir fan', 'a bowl of ramen'), ('a set of chopsticks', 'a train snack')],
                 2: [('a leather wallet', 'a scarf'), ('a pair of sunglasses', 'a cookbook')]}[skin]
        return dict(who=r.person(), skin=skin, p1=p1, p2=p2, rate=rate, items=r.pick(items), x=r.int(3, 9))

    fallback = dict(who=person('Hugo'), skin=0, p1=350, p2=200, rate=20,
                    items=('a woven blanket', 'a pair of sandals'), x=5)

    @staticmethod
    def solve(p):
        if p['skin'] == 2:
            return 100 * p['rate'] * p['p1'] + 100 * p['rate'] * p['p2']
        return F(100 * p['p1'], p['rate']) + F(100 * p['p2'], p['rate'])

    @staticmethod
    def render(p):
        w, p1, p2, rate, (i1, i2), x = p['who'], p['p1'], p['p2'], p['rate'], p['items'], p['x']
        P = p1 + p2
        if p['skin'] == 0:
            stem = (f"On a trip to Mexico, {w} exchanges money at a rate of 20 pesos per U.S. dollar. At an "
                    f"outdoor market, {w.he} buys {i1} for {num(p1)} pesos and {i2} for {num(p2)} pesos. {w.He} "
                    f"has {word(x)} days left on the trip.")
            steps = [f"Total: {num(p1)} + {num(p2)} = {num(P)} pesos.",
                     f"Each dollar is 20 pesos: {num(P)} ÷ 20 = {usd(P * 5)}."]
        elif p['skin'] == 1:
            stem = (f"{w} is visiting Japan, where 1 U.S. dollar is worth 150 yen that week. At a train station, "
                    f"{w.he} buys {i1} for {num(p1)} yen and {i2} for {num(p2)} yen. The station has "
                    f"{x + 6} platforms.")
            steps = [f"Total: {num(p1)} + {num(p2)} = {num(P)} yen.",
                     f"Each dollar is 150 yen: {num(P)} ÷ 150 = {P // 150} (check: 150 × {P // 150} = {num(P)}).",
                     f"So {w} spent {usd(P * 100 // 150)}."]
        else:
            stem = (f"{w} is traveling in Italy, where prices are in euros. That week, 1 euro costs "
                    f"{usd2(rate * 100)} in U.S. money. {w.He} buys {i1} for {p1} euros and {i2} for {p2} euros. "
                    f"{w.His} hotel is {x} blocks from the shop.")
            steps = [f"Total: {p1} + {p2} = {P} euros.",
                     f"Each euro is {usd2(rate * 100)}: {P} × {usd2(rate * 100)} = {usd(int(P * rate * 100))}."]
        return dict(stem=stem, ask=f"How much did {w} spend in all, in U.S. dollars?", steps=steps)
