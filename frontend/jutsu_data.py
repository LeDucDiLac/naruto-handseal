"""
Naruto Jutsu database — hand sign sequences, elements, and metadata.
"""

HAND_SIGNS = [
    "bird", "boar", "dog", "dragon", "hare", "horse",
    "monkey", "ox", "ram", "rat", "snake", "tiger"
]

ELEMENT_EMOJI = {
    "fire": "🔥", "lightning": "⚡", "water": "💧",
    "wind": "🌪️", "earth": "🪨", "special": "🟣",
}

SIGN_SYMBOLS = {
    "rat": "🐀", "ox": "🐂", "tiger": "🐅", "hare": "🐇",
    "dragon": "🐉", "snake": "🐍", "horse": "🐴", "ram": "🐏",
    "monkey": "🐒", "bird": "🐦", "dog": "🐕", "boar": "🐗",
}

JUTSU_DATABASE = [
    {
        "id": "fireball",
        "name": "Fire Release: Great Fireball Jutsu",
        "japanese_name": "火遁・豪火球の術 (Katon: Gōkakyū no Jutsu)",
        "element": "fire",
        "signs": ["snake", "ram", "monkey", "boar", "horse", "tiger"],
        "description": "A signature technique of the Uchiha clan. The user expels a massive orb of roaring flame.",
        "character": "Sasuke Uchiha",
        "difficulty": "intermediate",
        "effect_type": "fireball",
    },
    {
        "id": "chidori",
        "name": "Chidori (One Thousand Birds)",
        "japanese_name": "千鳥 (Chidori)",
        "element": "lightning",
        "signs": ["ox", "hare", "monkey"],
        "description": "A high concentration of lightning chakra channeled into the user's hand, sounding like a thousand birds.",
        "character": "Kakashi Hatake / Sasuke Uchiha",
        "difficulty": "advanced",
        "effect_type": "lightning",
    },
    {
        "id": "shadow_clone",
        "name": "Shadow Clone Jutsu",
        "japanese_name": "影分身の術 (Kage Bunshin no Jutsu)",
        "element": "special",
        "signs": ["ram"],
        "description": "Creates solid clones with their own chakra. Naruto's signature technique.",
        "character": "Naruto Uzumaki",
        "difficulty": "beginner",
        "effect_type": "clone",
    },
    {
        "id": "water_dragon",
        "name": "Water Release: Water Dragon Jutsu",
        "japanese_name": "水遁・水龍弾の術 (Suiton: Suiryūdan no Jutsu)",
        "element": "water",
        "signs": [
            "ox", "monkey", "hare", "rat", "boar", "bird", "ox", "horse",
            "bird", "rat", "tiger", "dog", "tiger", "snake", "ox", "ram",
            "snake", "boar", "ram", "rat", "monkey", "bird", "dragon",
            "bird", "ox", "horse", "ram", "tiger", "snake", "rat",
            "monkey", "hare", "boar", "dragon", "ram", "rat", "ox",
            "monkey", "bird", "rat", "boar", "bird",
        ],
        "description": "A powerful water technique requiring 42 hand seals. Creates a giant water dragon.",
        "character": "Zabuza Momochi / Kakashi Hatake",
        "difficulty": "legendary",
        "effect_type": "water",
    },
    {
        "id": "wind_scythe",
        "name": "Wind Release: Wind Scythe Jutsu",
        "japanese_name": "風遁・鎌鼬の術 (Fūton: Kamaitachi no Jutsu)",
        "element": "wind",
        "signs": ["rat"],
        "description": "Creates powerful gusts of cutting wind that slice through obstacles.",
        "character": "Temari",
        "difficulty": "beginner",
        "effect_type": "wind",
    },
]


def get_jutsu_by_id(jutsu_id: str) -> dict | None:
    return next((j for j in JUTSU_DATABASE if j["id"] == jutsu_id), None)

def get_jutsu_by_element(element: str) -> list[dict]:
    return [j for j in JUTSU_DATABASE if j["element"] == element]

def format_signs_display(signs: list[str]) -> str:
    return " → ".join(f"{SIGN_SYMBOLS.get(s, '❓')} {s.capitalize()}" for s in signs)

def get_difficulty_display(difficulty: str) -> str:
    colors = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴", "legendary": "🟣"}
    return f"{colors.get(difficulty, '⚪')} {difficulty.capitalize()}"
