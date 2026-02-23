import re

# Basic calorie database (per unit)
CALORIE_DB = {
    "rice": 200,
    "chapati": 120,
    "dal": 150,
    "egg": 70,
    "banana": 100,
    "milk": 120,
    "bread": 80,
    "apple": 95
}


def estimate_calories(text: str):
    text = text.lower()
    total_calories = 0

    for food, cal in CALORIE_DB.items():
        if food in text:
            quantity_match = re.search(rf"(\d+)\s*{food}", text)

            if quantity_match:
                quantity = int(quantity_match.group(1))
            else:
                quantity = 1

            total_calories += quantity * cal

    return total_calories