from flask import Flask, render_template, jsonify, request
from google_services import get_sheets_data, get_drive_files
from data_processor import process_sheets_data, build_creative_cards, sort_cards

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/creatives")
def api_creatives():
    days = int(request.args.get("days", 30))
    campaign_goal = request.args.get("campaign_goal", "") or None
    sort_by = request.args.get("sort_by", "revenue")
    search = request.args.get("search", "").strip().lower()

    try:
        raw_rows = get_sheets_data()
        drive_files = get_drive_files()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    perf_data = process_sheets_data(raw_rows, days=days, campaign_goal=campaign_goal)
    cards = build_creative_cards(perf_data, drive_files)

    if search:
        cards = [c for c in cards if search in c["creative_name"].lower()]

    cards = sort_cards(cards, sort_by=sort_by)

    return jsonify({"creatives": cards, "total": len(cards)})


@app.route("/api/refresh-cache")
def refresh_cache():
    try:
        get_drive_files(force_refresh=True)
        return jsonify({"status": "ok", "message": "Drive 캐시가 갱신되었습니다."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
