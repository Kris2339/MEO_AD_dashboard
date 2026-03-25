from datetime import datetime, timedelta
from collections import defaultdict
import config


def parse_date(date_str):
    """날짜 문자열을 datetime으로 변환 (여러 포맷 시도)"""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y", "%Y.%m.%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def safe_float(val):
    """문자열을 float으로 변환, 실패 시 0.0 반환"""
    if val is None:
        return 0.0
    try:
        return float(str(val).replace(",", "").replace(" ", "") or 0)
    except (ValueError, TypeError):
        return 0.0


def process_sheets_data(raw_rows, days=30, campaign_goal=None):
    """
    Sheets 데이터를 소재명 기준으로 집계
    반환: {소재명: {impressions, clicks, ctr, conversions, revenue, campaign_goal, latest_date}}
    """
    if not raw_rows:
        return {}

    cutoff = datetime.now() - timedelta(days=days)

    # 소재별 누적 데이터
    aggregated = defaultdict(
        lambda: {
            "impressions": 0.0,
            "clicks": 0.0,
            "conversions": 0.0,
            "revenue": 0.0,
            "campaign_goal": "",
            "latest_date": None,
        }
    )

    header_skipped = False
    for row in raw_rows:
        # 헤더 행 건너뛰기 (첫 번째 행이 숫자가 아닌 경우)
        if not header_skipped:
            header_skipped = True
            # H열(날짜)이 날짜 형식이 아니면 헤더로 간주
            if len(row) > config.COL_DATE and not parse_date(str(row[config.COL_DATE])):
                continue

        # 행 길이 체크
        max_col = max(
            config.COL_CAMPAIGN_GOAL,
            config.COL_CREATIVE_NAME,
            config.COL_DATE,
            config.COL_CONVERSION_VALUE,
        )
        if len(row) <= max_col:
            continue

        creative_name = str(row[config.COL_CREATIVE_NAME]).strip()
        if not creative_name:
            continue

        date_val = parse_date(str(row[config.COL_DATE]))
        if date_val is None or date_val < cutoff:
            continue

        goal = str(row[config.COL_CAMPAIGN_GOAL]).strip()

        # 캠페인 목표 필터
        if campaign_goal and goal != campaign_goal:
            continue

        impressions = safe_float(row[config.COL_IMPRESSIONS]) if len(row) > config.COL_IMPRESSIONS else 0.0
        clicks = safe_float(row[config.COL_CLICKS]) if len(row) > config.COL_CLICKS else 0.0
        conv_value = safe_float(row[config.COL_CONVERSION_VALUE])

        agg = aggregated[creative_name]
        agg["impressions"] += impressions
        agg["clicks"] += clicks
        agg["revenue"] += conv_value
        if not agg["campaign_goal"]:
            agg["campaign_goal"] = goal
        if agg["latest_date"] is None or date_val > agg["latest_date"]:
            agg["latest_date"] = date_val

    # CTR 계산 및 최종 정리
    result = {}
    for name, agg in aggregated.items():
        imp = agg["impressions"]
        clk = agg["clicks"]
        ctr = round((clk / imp * 100), 2) if imp > 0 else 0.0
        result[name] = {
            "creative_name": name,
            "impressions": int(imp),
            "clicks": int(clk),
            "ctr": ctr,
            "conversions": agg["conversions"],
            "revenue": round(agg["revenue"], 0),
            "campaign_goal": agg["campaign_goal"],
            "latest_date": agg["latest_date"].strftime("%Y-%m-%d") if agg["latest_date"] else "",
        }

    return result


def build_creative_cards(perf_data, drive_files):
    """성과 데이터와 Drive 파일을 매칭해서 카드 리스트 반환"""
    cards = []
    for name, perf in perf_data.items():
        drive_info = drive_files.get(name)
        if drive_info:
            file_id = drive_info["id"]
            embed_url = f"https://drive.google.com/file/d/{file_id}/preview"
            has_video = True
        else:
            embed_url = None
            has_video = False

        cards.append(
            {
                **perf,
                "has_video": has_video,
                "embed_url": embed_url,
            }
        )

    return cards


def sort_cards(cards, sort_by="revenue"):
    sort_map = {
        "ctr": lambda c: c["ctr"],
        "revenue": lambda c: c["revenue"],
        "conversions": lambda c: c["conversions"],
        "latest": lambda c: c["latest_date"],
    }
    key_fn = sort_map.get(sort_by, sort_map["revenue"])
    return sorted(cards, key=key_fn, reverse=True)
