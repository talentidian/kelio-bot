"""PTO / sick-day manager. Edits /data/pto.txt and /data/sick.txt."""
import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path

DATA_DIR = Path(os.environ.get("KELIO_DATA_DIR", "/data"))
PTO_FILE = DATA_DIR / "pto.txt"
SICK_FILE = DATA_DIR / "sick.txt"


def parse_arg(s: str) -> list[date]:
    if ".." in s:
        a, b = s.split("..")
        start, end = date.fromisoformat(a), date.fromisoformat(b)
        if end < start:
            raise ValueError("end before start")
        days = []
        cur = start
        while cur <= end:
            days.append(cur)
            cur += timedelta(days=1)
        return days
    return [date.fromisoformat(s)]


def load_dates(p: Path) -> set[date]:
    if not p.exists():
        return set()
    out = set()
    for raw in p.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        try:
            out.update(parse_arg(line))
        except ValueError:
            print(f"warn: bad line in {p.name}: {raw}", file=sys.stderr)
    return out


def save_dates(p: Path, dates: set[date]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    lines = [d.isoformat() for d in sorted(dates)]
    p.write_text("\n".join(lines) + ("\n" if lines else ""))


def is_pto_or_sick(d: date) -> tuple[bool, str]:
    if d in load_dates(PTO_FILE):
        return True, "PTO"
    if d in load_dates(SICK_FILE):
        return True, "sick"
    return False, ""


def cmd_add(args):
    days = parse_arg(args.spec)
    cur = load_dates(PTO_FILE)
    cur.update(days)
    save_dates(PTO_FILE, cur)
    print(f"added {len(days)} day(s). total PTO: {len(cur)}")


def cmd_remove(args):
    days = set(parse_arg(args.spec))
    cur = load_dates(PTO_FILE)
    removed = cur & days
    cur -= days
    save_dates(PTO_FILE, cur)
    print(f"removed {len(removed)} day(s). total PTO: {len(cur)}")


def cmd_list(args):
    today = date.today()
    upcoming = sorted(d for d in load_dates(PTO_FILE) if d >= today)
    if not upcoming:
        print("no upcoming PTO")
        return
    for d in upcoming:
        print(d.isoformat())


def cmd_sick(args):
    target = date.today() if args.spec == "today" else date.fromisoformat(args.spec)
    cur = load_dates(SICK_FILE)
    cur.add(target)
    save_dates(SICK_FILE, cur)
    print(f"marked sick: {target}")


def main():
    p = argparse.ArgumentParser(prog="pto")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="add PTO day(s) — YYYY-MM-DD or YYYY-MM-DD..YYYY-MM-DD")
    a.add_argument("spec")
    a.set_defaults(func=cmd_add)

    r = sub.add_parser("remove", help="remove PTO day(s)")
    r.add_argument("spec")
    r.set_defaults(func=cmd_remove)

    l = sub.add_parser("list", help="list upcoming PTO")
    l.set_defaults(func=cmd_list)

    s = sub.add_parser("sick", help="mark sick day (today or YYYY-MM-DD)")
    s.add_argument("spec", nargs="?", default="today")
    s.set_defaults(func=cmd_sick)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()