from datetime import date
import holidays

EXTRA_MADRID_CITY = {
    (5, 15),
    (11, 9),
}


def is_madrid_holiday(d: date) -> tuple[bool, str]:
    es_madrid = holidays.country_holidays("ES", subdiv="MD", years=d.year)
    if d in es_madrid:
        return True, es_madrid.get(d)
    if (d.month, d.day) in EXTRA_MADRID_CITY:
        label = "San Isidro" if (d.month, d.day) == (5, 15) else "Almudena"
        return True, label
    return False, ""


if __name__ == "__main__":
    import sys
    target = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    hit, name = is_madrid_holiday(target)
    print(f"{target}: {'HOLIDAY - ' + name if hit else 'working day'}")