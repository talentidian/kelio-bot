"""Run on Windows ONCE to capture Kelio auth state. Headed Chromium opens, you log in normally."""
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

KELIO_URL = os.environ.get("KELIO_URL", "https://signify.kelio.io/open/bwt/portail.jsp#clock_in_out")
OUT = Path(__file__).parent / "storage_state.json"


def main():
    print(f"opening {KELIO_URL} in a real Chromium window")
    print("log in normally with Signify SSO + MFA")
    print("once you land on the Kelio dashboard, come back here and press ENTER\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        ctx = browser.new_context(
            locale="es-ES",
            timezone_id="Europe/Madrid",
            geolocation={"latitude": 40.4392, "longitude": -3.6485, "accuracy": 30},
            permissions=["geolocation"],
        )
        page = ctx.new_page()
        page.goto(KELIO_URL)

        input("press ENTER once you're on the Kelio dashboard (clock-in button visible) > ")

        ctx.storage_state(path=str(OUT))
        print(f"\nsaved auth state to: {OUT}")
        print(f"current URL: {page.url}")
        print("\nselector pre-pinned: a[onclick*='BADGER_ES'] (Fichar una entrada/salida)")
        print("if you see the button on screen, you're good.")
        input("\npress ENTER to close browser > ")
        ctx.close()
        browser.close()


if __name__ == "__main__":
    sys.exit(main())