"""Push notifications via ntfy.sh. Silently no-ops if NTFY_TOPIC is unset."""
import os
import urllib.request

NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "")
NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh")


def post(title: str, message: str, priority: str = "default", tags: str = "") -> bool:
    if not NTFY_TOPIC:
        return False
    url = f"{NTFY_SERVER}/{NTFY_TOPIC}"
    safe_title = title.encode("ascii", "ignore").decode("ascii") or "Kelio"
    headers = {"Title": safe_title, "Priority": priority}
    if tags:
        headers["Tags"] = tags
    req = urllib.request.Request(
        url, data=message.encode("utf-8"), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return 200 <= r.status < 300
    except Exception:
        return False


if __name__ == "__main__":
    import sys
    title = sys.argv[1] if len(sys.argv) > 1 else "Kelio test"
    msg = sys.argv[2] if len(sys.argv) > 2 else "test notification"
    ok = post(title, msg, priority="default", tags="white_check_mark")
    print(f"sent: {ok} (topic={NTFY_TOPIC or '<unset>'})")