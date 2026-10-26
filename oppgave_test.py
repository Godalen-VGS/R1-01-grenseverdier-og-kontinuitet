"""Automatisk retting av R1-01-grenseverdier-og-kontinuitet.

Hver sjekk i SJEKKER er én deltest, og poengene fordeles likt på dem.
De samme sjekkene ligger i "Test løsningen din"-cellen nederst i notebooken.
"""
import pytest

from notebook_loader import last_notebook

def naer(a, b, rel=1e-3):
    """Sant hvis tallet a er innenfor rel (relativt) av b."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) <= rel * abs(b)


def S(tekst):
    """Gjør tekst om til et sympy-uttrykk, f.eks. S("x**2 - 1")."""
    import sympy
    return sympy.sympify(tekst, locals={n: sympy.Symbol(n) for n in ("N", "O", "Q", "S")})


def lik(a, b):
    """Sant hvis a og b er matematisk like.

    Lister og mengder sammenlignes uten hensyn til rekkefølge, tupler (koordinater) i rekkefølge.
    """
    import sympy
    if a is None:
        return False
    if isinstance(b, tuple):
        if not isinstance(a, (tuple, list, sympy.Tuple)) or len(a) != len(b):
            return False
        return all(lik(x, y) for x, y in zip(a, b))
    if isinstance(b, (list, set)):
        if isinstance(a, sympy.FiniteSet):
            a = list(a)
        if not isinstance(a, (list, tuple, set)) or len(a) != len(b):
            return False
        rest = list(a)
        for y in b:
            for i, x in enumerate(rest):
                if lik(x, y):
                    del rest[i]
                    break
            else:
                return False
        return True
    if isinstance(b, dict):
        if not isinstance(a, dict) or len(a) != len(b):
            return False
        a = {str(k): v for k, v in a.items()}
        return all(str(k) in a and lik(a[str(k)], v) for k, v in b.items())
    try:
        a, b = sympy.sympify(a), sympy.sympify(b)
    except (sympy.SympifyError, TypeError):
        return False
    vanlige = lambda u: u.subs({s: sympy.Symbol(s.name) for s in u.free_symbols})
    a, b = vanlige(a), vanlige(b)
    if isinstance(a, sympy.Set) or isinstance(b, sympy.Set):
        return a == b
    if getattr(b, "is_Relational", False):
        return a == b
    try:
        return sympy.simplify(a - b) == 0
    except TypeError:
        return a == b

oppgave = last_notebook("oppgave")

SJEKKER = [
    ('1_hull', 'numerisk_grense((x² - 9)/(x - 3), 3) skal gi ca. 6', 'naer(numerisk_grense(lambda x: (x**2 - 9)/(x - 3), 3), 6, rel=1e-5)'),
    ('1_annen', 'numerisk_grense((x³ - 1)/(x - 1), 1) skal gi ca. 3', 'naer(numerisk_grense(lambda x: (x**3 - 1)/(x - 1), 1), 3, rel=1e-5)'),
    ('2a', 'g_2a skal være 1', 'lik(g_2a, 1)'),
    ('2b', 'g_2b skal være 2/5', "lik(g_2b, S('2/5'))"),
    ('2c', 'g_2c skal være 1/2', "lik(g_2c, S('1/2'))"),
    ('3', 'venstre og hoyre skal være -1 og 1, og grensen finnes ikke', 'lik(venstre, -1) and lik(hoyre, 1) and grensen_finnes == False'),
    ('4', 'a_kontinuerlig skal være 3', 'lik(a_kontinuerlig, 3)'),
    ('5_ja', 'er_kontinuerlig(x² + 1, 3x - 1, 2) skal gi True', "er_kontinuerlig(S('x**2 + 1'), S('3*x - 1'), 2) == True"),
    ('5_nei', 'er_kontinuerlig(x², x + 1, 1) skal gi False', "er_kontinuerlig(S('x**2'), S('x + 1'), 1) == False and er_kontinuerlig(S('x'), S('2*x - 1'), 1) == True"),
]


@pytest.mark.parametrize(
    "beskrivelse,uttrykk", [s[1:] for s in SJEKKER], ids=[s[0] for s in SJEKKER]
)
def test_sjekk(beskrivelse, uttrykk):
    navnerom = {**vars(oppgave), "naer": naer, "lik": lik, "S": S}
    assert eval(uttrykk, navnerom), beskrivelse
