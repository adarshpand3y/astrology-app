"""Naisargika, tatkalika and panchadha (compound) planetary relationships."""
from .constants import NATURAL_RELATIONS

GREAT_FRIEND, FRIEND, NEUTRAL, ENEMY, GREAT_ENEMY = (
    "great_friend", "friend", "neutral", "enemy", "great_enemy")


def natural(a: str, b: str) -> int:
    """+1 friend, 0 neutral, -1 enemy (from a's point of view)."""
    friends, neutrals, _ = NATURAL_RELATIONS[a]
    if b in friends:
        return 1
    if b in neutrals:
        return 0
    return -1


def temporary(sign_a: int, sign_b: int) -> int:
    """+1 if b is in 2,3,4,10,11,12 from a, else -1."""
    house = (sign_b - sign_a) % 12 + 1
    return 1 if house in (2, 3, 4, 10, 11, 12) else -1


_COMPOUND = {2: GREAT_FRIEND, 1: FRIEND, 0: NEUTRAL, -1: ENEMY, -2: GREAT_ENEMY}


def compound(a: str, b: str, signs: dict[str, int]) -> str:
    return _COMPOUND[natural(a, b) + temporary(signs[a], signs[b])]


def compound_table(planets: list[str], signs: dict[str, int]) -> dict[str, dict[str, str]]:
    return {a: {b: compound(a, b, signs) for b in planets if b != a} for a in planets}
