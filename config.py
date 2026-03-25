# Google API 설정
CREDENTIALS_FILE = "credentials.json"

# Google Sheets 설정
SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"
SHEET_NAME = "30일"

# 열 인덱스 (0-based)
COL_CAMPAIGN_GOAL = 2   # C열: 캠페인 목표
COL_CREATIVE_NAME = 5   # F열: 소재명
COL_DATE = 7            # H열: 날짜
COL_IMPRESSIONS = 8     # I열: 노출수 (필요시 수정)
COL_CLICKS = 9          # J열: 클릭수 (필요시 수정)
COL_CONVERSION_VALUE = 10  # K열: 매출 또는 전환값

# Google Drive 설정
DRIVE_FOLDER_ID = "YOUR_DRIVE_FOLDER_ID_HERE"

# 캐시 설정 (초)
DRIVE_CACHE_TTL = 300  # 5분
