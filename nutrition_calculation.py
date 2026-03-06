# nutrition_targets.py
from dataclasses import dataclass
from typing import Optional, Dict

ACTIVITY_MULTIPLIER = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "vigorous": 1.725,
}

def clamp(n: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, n))

def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    return base + 5 if gender == "male" else base - 161

def calorie_adjustment(goal: str) -> int:
    return {
        "weight_loss": -500,
        "muscle_gain": 300,
        "maintenance": 0,
        "low_sugar": 0,
    }.get(goal, 0)

def protein_multiplier(goal: str) -> float:
    return {
        "weight_loss": 2.0,
        "muscle_gain": 2.2,
        "maintenance": 1.6,
        "low_sugar": 1.8,
    }.get(goal, 1.6)

def fat_percentage(goal: str) -> float:
    return {
        "weight_loss": 0.30,
        "low_sugar": 0.30,
        "muscle_gain": 0.25,
        "maintenance": 0.28,
    }.get(goal, 0.28)

def sugar_target_g(goal: str, gender: str, calories: int) -> float:
    if goal == "low_sugar":
        return 25.0 if gender == "male" else 20.0

    ten_percent = (calories * 0.10) / 4.0  # grams
    typical_cap = 36.0 if gender == "male" else 25.0
    return float(min(ten_percent, typical_cap))

def fiber_target_g(gender: str, calories: int) -> float:
    from_cals = (calories / 1000.0) * 14.0
    minimum = 38.0 if gender == "male" else 25.0
    return float(max(from_cals, minimum))

def sodium_target_mg(goal: str) -> float:
    return 2000.0 if goal == "weight_loss" else 2300.0

def water_target_glasses(weight_kg: float, activity_level: str) -> int:
    liters = weight_kg * 0.033
    mult = ACTIVITY_MULTIPLIER.get(activity_level, 1.2)
    if mult >= 1.55:
        liters += 0.5
    if mult >= 1.725:
        liters += 0.5
    glasses = round((liters * 1000) / 250)  # 250ml/glass
    return max(4, glasses)

def calculate_targets(profile: Dict, calorie_override: Optional[int] = None) -> Dict:
    """
    profile must include:
      age, gender, weight_kg, height_cm, activity_level, dietary_goal
    calorie_override: if provided, calories are set to this and macros rebalanced.
    """

    age = int(profile["age"])
    gender = profile["gender"]
    weight_kg = float(profile["weight_kg"])
    height_cm = float(profile["height_cm"])
    activity_level = profile["activity_level"]
    goal = profile["dietary_goal"]

    # Calories
    if calorie_override is not None:
        calories = int(round(calorie_override))
    else:
        bmr = calculate_bmr(weight_kg, height_cm, age, gender)
        tdee = bmr * ACTIVITY_MULTIPLIER.get(activity_level, 1.2)
        calories = int(round(tdee + calorie_adjustment(goal)))

    #  bounds for calories to prevent it being too low or too high
    calories = int(clamp(calories, 1200, 4500))

    # --- Macros to prevent against negative carbs
    MIN_CARBS_G = 50.0
    MIN_FAT_PCT = 0.20
    MIN_PROTEIN_MULT = 1.6

    prot_mult = protein_multiplier(goal)
    fat_pct = fat_percentage(goal)

    def macro_calc(prot_m: float, fat_p: float):
        protein_g = weight_kg * prot_m
        protein_cals = protein_g * 4.0

        fat_cals = calories * fat_p
        fat_g = fat_cals / 9.0

        carbs_cals = calories - protein_cals - fat_cals
        carbs_g = carbs_cals / 4.0
        return protein_g, fat_g, carbs_g

    protein_g, fat_g, carbs_g = macro_calc(prot_mult, fat_pct)

    # Step 1: if carbs too low, lower fat% down to MIN_FAT_PCT
    if carbs_g < MIN_CARBS_G and fat_pct > MIN_FAT_PCT:
        fat_pct = MIN_FAT_PCT
        protein_g, fat_g, carbs_g = macro_calc(prot_mult, fat_pct)

    # Step 2: if still too low, lower protein multiplier down to MIN_PROTEIN_MULT
    if carbs_g < MIN_CARBS_G and prot_mult > MIN_PROTEIN_MULT:
        prot_mult = MIN_PROTEIN_MULT
        protein_g, fat_g, carbs_g = macro_calc(prot_mult, fat_pct)

    # Step 3: final clamp (keep at least MIN_CARBS_G by slightly reducing fat grams if needed)
    if carbs_g < MIN_CARBS_G:
        # Force carbs to MIN_CARBS_G by taking calories from fat first 
        target_carbs_cals = MIN_CARBS_G * 4.0
        protein_cals = protein_g * 4.0
        remaining_for_fat = calories - protein_cals - target_carbs_cals
        remaining_for_fat = max(0.0, remaining_for_fat)
        fat_g = remaining_for_fat / 9.0
        carbs_g = MIN_CARBS_G

    targets = {
        "calorie_target": calories,
        "protein_target_g": round(protein_g, 2),
        "carbs_target_g": round(carbs_g, 2),
        "fat_target_g": round(fat_g, 2),
        "sugar_target_g": round(sugar_target_g(goal, gender, calories), 2),
        "fiber_target_g": round(fiber_target_g(gender, calories), 2),
        "sodium_target_mg": round(sodium_target_mg(goal), 2),
        "water_target_glasses": int(water_target_glasses(weight_kg, activity_level)),
    }
    return targets