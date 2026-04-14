export const HAND_SIGNS = [
  "bird", "boar", "dog", "dragon", "hare", "horse",
  "monkey", "ox", "ram", "rat", "snake", "tiger"
];

export const SIGN_SYMBOLS = {
  "rat": "🐀", "ox": "🐂", "tiger": "🐅", "hare": "🐇",
  "dragon": "🐉", "snake": "🐍", "horse": "🐴", "ram": "🐏",
  "monkey": "🐒", "bird": "🐦", "dog": "🐕", "boar": "🐗",
};

export const JUTSU_DATABASE = [
  {
      "id": "fireball",
      "name": "Great Fireball Jutsu",
      "element": "fire",
      "signs": ["snake", "ram", "monkey", "boar", "horse", "tiger"],
      "difficulty": "intermediate",
      "effect_type": "fireball",
  },
  {
      "id": "chidori",
      "name": "Chidori",
      "element": "lightning",
      "signs": ["ox", "hare", "monkey"],
      "difficulty": "advanced",
      "effect_type": "lightning",
  },
  {
      "id": "shadow_clone",
      "name": "Shadow Clone Jutsu",
      "element": "special",
      "signs": ["ram"],
      "difficulty": "beginner",
      "effect_type": "clone",
  },
  {
      "id": "water_dragon",
      "name": "Water Dragon Jutsu",
      "element": "water",
      "signs": [
          "ox", "monkey", "hare", "rat", "boar", "bird", "ox", "horse",
          "bird", "rat", "tiger", "dog", "tiger", "snake", "ox", "ram",
          "snake", "boar", "ram", "rat", "monkey", "bird", "dragon",
          "bird", "ox", "horse", "ram", "tiger", "snake", "rat",
          "monkey", "hare", "boar", "dragon", "ram", "rat", "ox",
          "monkey", "bird", "rat", "boar", "bird",
      ],
      "difficulty": "legendary",
      "effect_type": "water",
  },
  {
      "id": "wind_scythe",
      "name": "Wind Scythe Jutsu",
      "element": "wind",
      "signs": ["rat"],
      "difficulty": "beginner",
      "effect_type": "wind",
  },
];
