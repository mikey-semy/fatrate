import random

def get_fat_prefix(l10n, position: int, total: int, bmi: float) -> str:
    fat_leader = ['mega', 'titan', 'god', 'boss', 'king', 'lord', 'master', 'supreme', 'emperor', 'chief']
    skinny_leader = ['stick', 'ghost', 'air', 'zero', 'void', 'nothing', 'quantum', 'shadow', 'paper', 'dust']
    
    middle_attrs = ['norm', 'chad', 'sigma', 'based', 'boss', 'king', 'flex', 'alpha', 'giga', 'top']
    fat_attrs = ['pig', 'blob', 'food', 'sofa', 'mass', 'burger', 'champ', 'ham', 'mayo', 'chunk']
    skinny_attrs = ['stick', 'wind', 'bone', 'dry', 'zero', 'leaf', 'match', 'noodle', 'snake', 'dust']
    
    if position == 1:
        attr = random.choice(fat_leader)
        key = f"fat-leader-prefix-{attr}"
        return l10n.format_value(key)
    elif position == total:
        attr = random.choice(skinny_leader)
        key = f"skinny-leader-prefix-{attr}"
        return l10n.format_value(key)
    else:
        if bmi > 25:  # Избыточный вес
            attr = random.choice(fat_attrs)
            key = f"fat-prefix-{attr}"
            return l10n.format_value(key)
        elif bmi < 18.5:  # Недостаточный вес
            attr = random.choice(skinny_attrs)
            key = f"skinny-prefix-{attr}"
            return l10n.format_value(key)
        else:  # Нормальный вес
            attr = random.choice(middle_attrs)
            key = f"middle-prefix-{attr}"
            return l10n.format_value(key)

def get_bmi_status(bmi: float) -> str:
    if bmi == 0.0:
        return "weight-not-specified"
    elif bmi <= 16.0:
        return "severe-underweight"
    elif bmi <= 18.5:
        return "underweight"
    elif bmi <= 25.0:
        return "normal-weight"
    elif bmi <= 30.0:
        return "overweight"
    elif bmi <= 35.0:
        return "obesity-1"
    elif bmi <= 40.0:
        return "obesity-2"
    else:
        return "obesity-3"