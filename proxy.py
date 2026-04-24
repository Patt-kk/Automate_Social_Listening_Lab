"""
Local CORS proxy for ask-dom.com
Run: pip install flask flask-cors httpx && python proxy.py
Then open dom_dashboard.html in your browser.
"""

import httpx
from flask import Flask, request, Response, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=True)

BASE_URL = "https://app.ask-dom.com"
session  = httpx.Client(follow_redirects=True, timeout=30)

PROXY_PATHS = [
    "/login",
    "/get-all",
    "/get-current-credit",
    "/get-account-category",
    "/campaign",
    "/user-preset-campaign",
    "/stats",
    "/categroy-compare",
    "/category-pie",
    "/category-history",
    "/category-sov",
    "/overall",
]

@app.route("/proxy/<path:subpath>", methods=["GET", "POST", "OPTIONS"])
def proxy(subpath):
    if request.method == "OPTIONS":
        return _cors_preflight()

    target_url = f"{BASE_URL}/{subpath}"
    params     = dict(request.args)
    headers    = {
        k: v for k, v in request.headers
        if k.lower() not in ("host", "content-length", "origin", "referer")
    }

    try:
        if request.method == "POST":
            r = session.post(target_url, data=request.form, params=params, headers=headers)
        else:
            r = session.get(target_url, params=params, headers=headers)

        content_type = r.headers.get("content-type", "application/json")
        return Response(
            r.content,
            status=r.status_code,
            content_type=content_type,
            headers={
                "Access-Control-Allow-Origin":      "*",
                "Access-Control-Allow-Credentials": "true",
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _cors_preflight():
    return Response("", status=204, headers={
        "Access-Control-Allow-Origin":  "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    })


if __name__ == "__main__":
    print("\n✅  DOM Proxy running at http://localhost:5055")
    print("   Open dom_dashboard.html in your browser\n")
    app.run(port=5055, debug=False)
