import json
import sys
import urllib.request


def post_alert(api_url: str, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        response.read()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m app.ingest_adapter http://localhost:8000/api/alerts/ingest")
        sys.exit(1)
    api_url = sys.argv[1]

    for line in sys.stdin:
        if not line.strip():
            continue
        payload = json.loads(line)
        post_alert(api_url, payload)


if __name__ == "__main__":
    main()
