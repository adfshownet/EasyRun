"""Serve the static EasyRun prototype locally for manual inspection."""

import argparse
import http.server
import socketserver
import webbrowser
from pathlib import Path

PROTOTYPE_DIR = Path(__file__).resolve().parents[2] / "prototype"


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--no-browser", action="store_true", help="Don't auto-open the browser")
    args = parser.parse_args()

    handler = lambda *a, **kw: NoCacheHandler(*a, directory=str(PROTOTYPE_DIR), **kw)
    url = f"http://localhost:{args.port}/EasyRun.dc.html"

    with socketserver.TCPServer(("localhost", args.port), handler) as httpd:
        print(f"Serving {PROTOTYPE_DIR} at {url} (Ctrl+C to stop)")
        if not args.no_browser:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
