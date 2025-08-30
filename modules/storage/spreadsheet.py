from typing import List
import gspread
from config import load_env
from datetime import datetime
from modules.models.article import Article

ENV = load_env()
GOOGLE_SHEET_KEY = ENV.get("GOOGLE_SHEET_KEY")
SERVICE_ACCOUNT_FILE = ENV.get("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")  # 기본값 root/service_account.json


def _get_worksheet(set_name: str):
    """
    스프레드시트 연결 후 워크시트 객체 반환
    """
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_KEY)

    # 워크시트 이름: set_name, 없으면 새로 생성
    try:
        worksheet = sheet.worksheet(set_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sheet.add_worksheet(title=set_name, rows="1000", cols="20")

    return worksheet


def save_news(set_name: str, news_list: List[Article]):
    """
    dict 타입 뉴스 리스트를 스프레드시트에 저장
    :param news_list: [{'title':..., 'url':..., 'content':..., 'publishedAt':...}, ...]
    """
    if not GOOGLE_SHEET_KEY:
        raise ValueError("❌ GOOGLE_SHEET_KEY가 설정되지 않았습니다 (.env 확인 필요)")

    worksheet = _get_worksheet(set_name=set_name)

    # 스프레드시트에 헤더가 없으면 추가
    if worksheet.row_count == 0 or not worksheet.cell(1, 1).value:
        worksheet.append_row(["title", "content", "url", "source", "subject", "used"])

    saved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows = []
    for news in news_list:
        rows.append([
            news.title,
            news.content,
            news.url,
            news.source,
            news.subject
        ])

    # 한 번에 여러 행 추가
    worksheet.append_rows(rows)
    print(f"[Spreadsheet] 뉴스 {len(news_list)}개 저장 완료")
