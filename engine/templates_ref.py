"""Reference templates. Read these first: they show the house style and the contract."""
from fractions import Fraction as F

from engine import Retry, template, person, usd, num, pct, plural, word, cap, a_an


@template(id='t2.packs-or-singles.v1', tier=2, topic='money', kind='money', seconds=60)
class PacksOrSingles:
    # Context: (item, plural, pack word, who it's for, event, irrelevant detail)
    CONTEXTS = [
        ('bagel', 'bagels', 'bakery', "team's {t} meeting", 'people are coming'),
        ('donut', 'donuts', 'donut shop', "class's {t} study session", 'students signed up'),
        ('sandwich', 'sandwiches', 'deli', "{t} volunteer shift at the food bank", 'volunteers are on the list'),
    ]

    @staticmethod
    def params(r):
        k = r.pick([4, 6])                      # pack size
        single = r.pick([85, 90, 95, 110, 125])  # cents per single item
        # pack is a bit cheaper per item than singles
        pack = r.pick([k * single - d for d in (40, 60, 75, 90, 120, 150)])
        if pack % 25:
            raise Retry
        n = r.int(9, 23)
        if n % k == 0:
            raise Retry
        q, rem = divmod(n, k)
        a, b = q * pack + rem * single, (q + 1) * pack
        if a == b:
            raise Retry
        return dict(who=r.person(), ctx=r.pick(PacksOrSingles.CONTEXTS), k=k, single=single, pack=pack, n=n,
                    t=r.pick(['8 a.m.', '9:30 a.m.', '7:45 a.m.', 'noon']))

    fallback = dict(who=person('Rosa'), ctx=CONTEXTS[0], k=4, single=95, pack=300, n=11, t='8 a.m.')

    @staticmethod
    def solve(p):
        # brute force every possible number of packs
        return min(m * p['pack'] + max(0, p['n'] - m * p['k']) * p['single'] for m in range(0, p['n'] // p['k'] + 2))

    @staticmethod
    def render(p):
        w, (it, its, shop, event, coming) = p['who'], p['ctx']
        k, n, pack, single = p['k'], p['n'], p['pack'], p['single']
        q, rem = divmod(n, k)
        a, b = q * pack + rem * single, (q + 1) * pack
        stem = (f"{w} is picking up {its} for the {event.format(t=p['t'])}. The {shop} sells {its} in packs of "
                f"{k} for {usd(pack)}, or one at a time for {usd(single)} each. {cap(word(n))} {coming}, and {w} wants "
                f"at least one {it} per person. Leftovers are fine, but {w.he} can't split a pack.")
        steps = [
            f"{n} ÷ {k} = {q} full packs, with {plural(rem, 'person', 'people')} left over.",
            f"Option 1: {q} packs + {plural(rem, 'single')} = {usd(q * pack)} + {usd(rem * single)} = {usd(a)}.",
            f"Option 2: {q + 1} packs = {usd(b)}, with {(q + 1) * k - n} extra.",
            f"The cheaper option is {usd(min(a, b))}.",
        ]
        return dict(stem=stem, ask=f"What is the least {w} can spend?", steps=steps)


@template(id='t3.final-exam-needed.v1', tier=3, topic='averages', kind='int', unit='points', seconds=75)
class FinalExamNeeded:
    COURSES = ['chemistry', 'statistics', 'world history', 'economics', 'biology']

    @staticmethod
    def params(r):
        w = r.pick([(20, 20, 30, 30), (10, 30, 30, 30), (20, 30, 20, 30), (10, 20, 30, 40)])
        hw, qz, mid = r.int(80, 98), r.int(72, 95), r.int(68, 92)
        target = r.pick([80, 85, 88, 90])
        need = F(target * 100 - w[0] * hw - w[1] * qz - w[2] * mid, w[3])
        if need.denominator != 1 or not 70 <= need <= 100:
            raise Retry
        return dict(who=r.person(), course=r.pick(FinalExamNeeded.COURSES), w=w, hw=hw, qz=qz, mid=mid,
                    target=target, size=r.int(18, 34))

    fallback = dict(who=person('Priya'), course='chemistry', w=(20, 20, 30, 30), hw=90, qz=80, mid=80, target=85,
                    size=26)

    @staticmethod
    def solve(p):
        w = p['w']
        have = F(w[0] * p['hw'] + w[1] * p['qz'] + w[2] * p['mid'], 100)
        return (p['target'] - have) / F(w[3], 100)

    @staticmethod
    def render(p):
        w, who = p['w'], p['who']
        parts = [w[0] * F(p['hw'], 100), w[1] * F(p['qz'], 100), w[2] * F(p['mid'], 100)]
        have = sum(parts)
        need_pts = p['target'] - have
        stem = (f"{who}'s {p['course']} grade is a weighted average of four categories. The table shows each "
                f"category's weight and {who.his} average so far. There are {p['size']} students in the class, and "
                f"only the final exam is left.")
        table = dict(headers=['Category', 'Weight', 'Average'],
                     rows=[['Homework', pct(w[0]), p['hw']], ['Quizzes', pct(w[1]), p['qz']],
                           ['Midterm', pct(w[2]), p['mid']], ['Final exam', pct(w[3]), '?']])
        steps = [
            f"Points earned so far: {num(parts[0])} + {num(parts[1])} + {num(parts[2])} = {num(have)}.",
            f"To finish at {p['target']}, the final must add {p['target']} − {num(have)} = {num(need_pts)} points.",
            f"The final is worth {w[3]}%, so the score needed is {num(need_pts)} ÷ {num(F(w[3], 100))} = "
            f"{num(need_pts / F(w[3], 100))}.",
        ]
        return dict(stem=stem, table=table,
                    ask=f"What score does {who} need on the final exam to finish with exactly {a_an(p['target'])}?",
                    steps=steps)
