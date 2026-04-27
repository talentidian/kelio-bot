"""Kelio clock-in/out runner. Invoked by cron with --action in|out."""
import argparse
import os
import random
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from playwright.sync_api import sync_playwright

from holidays_check import is_madrid_holiday
from pto import is_pto_or_sick
import notify

DATA_DIR = Path(os.environ.get("KELIO_DATA_DIR", "/data"))
STATE_FILE = DATA_DIR / "storage_state.json"
KELIO_URL = os.environ.get("KELIO_URL", "https://signify.kelio.io")
BUTTON_SELECTOR = os.environ.get("KELIO_CLOCK_BUTTON_SELECTOR", 'a[onclick*="BADGER_ES"]')
KELIO_LAT = float(os.environ.get("KELIO_LAT", "40.4392"))
KELIO_LON = float(os.environ.get("KELIO_LON", "-3.6485"))
TZ = ZoneInfo(os.environ.get("TZ", "Europe/Madrid"))


def log(msg: str) -> None:
    print(f"[{datetime.now(TZ).isoformat(timespec='seconds')}] {msg}", flush=True)


def should_skip_today() -> tuple[bool, str]:
    today = datetime.now(TZ).date()
    weekday = today.weekday()
    if weekday >= 5:
        return True, "weekend"
    hit, name = is_madrid_holiday(today)
    if hit:
        return True, f"holiday: {name}"
    hit, name = is_pto_or_sick(today)
    if hit:
        return True, name
    return False, ""


def jitter_sleep() -> None:
    delay = random.uniform(30, 90)
    log(f"jitter sleep {delay:.1f}s")
    time.sleep(delay)


def maybe_warn_aging_auth() -> None:
    if not STATE_FILE.exists():
        return
    now = datetime.now(TZ)
    if now.weekday() != 0 or now.hour > 9:
        return
    age_days = (time.time() - STATE_FILE.stat().st_mtime) / 86400
    if age_days < 50:
        return
    notify.post(
        "Kelio auth aging",
        f"storage_state.json is {age_days:.0f} days old. Run /kelio reauth before it expires.",
        priority="default",
        tags="hourglass",
    )


def run_punch(action: str, dry_run: bool = False) -> int:
    if not STATE_FILE.exists():
        log(f"FATAL: no auth state at {STATE_FILE} — run login.py locally and upload")
        return 2
    if not BUTTON_SELECTOR:
        log("FATAL: KELIO_CLOCK_BUTTON_SELECTOR env var is empty")
        return 2

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            storage_state=str(STATE_FILE),
            locale="es-ES",
            timezone_id="Europe/Madrid",
            viewport={"width": 1366, "height": 900},
            geolocation={"latitude": KELIO_LAT, "longitude": KELIO_LON, "accuracy": 30},
            permissions=["geolocation"],
        )
        page = ctx.new_page()
        try:
            log(f"navigating to {KELIO_URL}")
            page.goto(KELIO_URL, wait_until="domcontentloaded", timeout=60_000)

            if "login" in page.url.lower() or "signin" in page.url.lower() or "microsoftonline" in page.url.lower():
                log(f"FATAL: redirected to login — auth state expired. URL={page.url}")
                page.screenshot(path=str(DATA_DIR / "expired_auth.png"))
                return 3

            log(f"loaded page: {page.url}")
            log(f"page title: {page.title()}")
            btn = page.locator(BUTTON_SELECTOR).first
            btn.wait_for(state="visible", timeout=30_000)
            try:
                btn_text = btn.inner_text(timeout=3_000).strip()
            except Exception:
                btn_text = "?"
            log(f"button found, text: {btn_text!r}")
            if dry_run:
                log("DRY RUN - not clicking")
                page.screenshot(path=str(DATA_DIR / "dry_run.png"), full_page=False)
                ctx.storage_state(path=str(STATE_FILE))
                return 0
            log(f"clicking [{action}] at ({KELIO_LAT}, {KELIO_LON})")
            btn.click()
            page.wait_for_load_state("networkidle", timeout=15_000)
            page.wait_for_timeout(2000)
            try:
                page.screenshot(path=str(DATA_DIR / f"last_{action}.png"), full_page=False)
            except Exception:
                pass
            log(f"punch {action} OK")

            ctx.storage_state(path=str(STATE_FILE))
            return 0
        except Exception as e:
            log(f"ERROR during {action}: {e}")
            traceback.print_exc()
            try:
                page.screenshot(path=str(DATA_DIR / f"error_{action}.png"))
            except Exception:
                pass
            return 1
        finally:
            ctx.close()
            browser.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--action", choices=["in", "out"], required=True)
    p.add_argument("--no-skip-check", action="store_true", help="run even on holidays/PTO")
    p.add_argument("--no-jitter", action="store_true", help="skip random delay (for manual runs)")
    p.add_argument("--dry-run", action="store_true", help="load page + verify button, don't click")
    args = p.parse_args()

    log(f"=== kelio_clock --action {args.action} ===")

    if not args.no_skip_check:
        skip, reason = should_skip_today()
        if skip:
            log(f"skipping: {reason}")
            return 0

    maybe_warn_aging_auth()

    if not args.no_jitter and not args.dry_run:
        jitter_sleep()

    result = run_punch(args.action, dry_run=args.dry_run)
    if result != 0 and not args.dry_run:
        if result == 3:
            notify.post(
                "Kelio auth EXPIRED",
                f"Punch {args.action} failed: SSO session expired. Run /kelio reauth.",
                priority="high",
                tags="rotating_light",
            )
        else:
            notify.post(
                f"Kelio punch {args.action} FAILED",
                f"exit={result}. Check logs: flyctl logs -a kelio-bot",
                priority="high",
                tags="warning",
            )
    return result


if __name__ == "__main__":
    sys.exit(main())