import time
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import config

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

_drive_cache = {"files": None, "timestamp": 0}


def get_credentials():
    return Credentials.from_service_account_file(config.CREDENTIALS_FILE, scopes=SCOPES)


def get_sheets_data():
    creds = get_credentials()
    client = gspread.authorize(creds)
    sheet = client.open_by_key(config.SPREADSHEET_ID).worksheet(config.SHEET_NAME)
    return sheet.get_all_values()


def get_drive_files(force_refresh=False):
    now = time.time()
    if (
        not force_refresh
        and _drive_cache["files"] is not None
        and now - _drive_cache["timestamp"] < config.DRIVE_CACHE_TTL
    ):
        return _drive_cache["files"]

    creds = get_credentials()
    service = build("drive", "v3", credentials=creds)

    files = {}
    page_token = None
    while True:
        response = (
            service.files()
            .list(
                q=f"'{config.DRIVE_FOLDER_ID}' in parents and trashed=false",
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=page_token,
                pageSize=1000,
            )
            .execute()
        )
        for f in response.get("files", []):
            # 확장자 제거한 파일명을 키로 사용
            name_no_ext = f["name"].rsplit(".", 1)[0] if "." in f["name"] else f["name"]
            files[name_no_ext] = {"id": f["id"], "name": f["name"], "mimeType": f["mimeType"]}
            # 원본 파일명도 키로 등록 (중복 방지)
            if f["name"] not in files:
                files[f["name"]] = {"id": f["id"], "name": f["name"], "mimeType": f["mimeType"]}

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    _drive_cache["files"] = files
    _drive_cache["timestamp"] = now
    return files
