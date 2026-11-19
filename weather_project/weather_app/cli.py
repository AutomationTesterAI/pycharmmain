"""Command-line entry point for running the local weather dashboard."""

import argparse
from threading import Timer
import webbrowser

from weather_app.app import create_app


def parse_args() -> argparse.Namespace:
    """Parse local server options."""
    parser = argparse.ArgumentParser(description="Run the local Weather Dashboard.")
    parser.add_argument("--host", default="127.0.0.1", help="Interface to bind to.")
    parser.add_argument("--port", default=8001, type=int, help="Port to listen on.")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open the dashboard in a browser automatically.",
    )
    return parser.parse_args()


def main() -> int:
    """Start the dashboard server and open it in a browser unless disabled."""
    args = parse_args()
    app = create_app()
    url = f"http://{args.host}:{args.port}"

    print(f"Weather Dashboard is available at {url}")
    print("Press Ctrl+C to stop the server.")
    if not args.no_browser:
        browser_timer = Timer(1, webbrowser.open, args=(url,))
        browser_timer.daemon = True
        browser_timer.start()

    app.run(host=args.host, port=args.port, debug=False, threaded=True)
    return 0
