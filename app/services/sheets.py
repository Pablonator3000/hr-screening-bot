import gspread
from google.oauth2.service_account import Credentials
import logging
from typing import List
from datetime import datetime

logger = logging.getLogger(__name__)

class SheetsClient:
    def __init__(self, credentials_path: str, sheet_id: str):
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id
        self.client = None
        self.sheet = None

    def connect(self):
        """Initializes connection to Google Sheets API."""
        if not self.credentials_path or not self.sheet_id:
            logger.warning("Google Sheets credentials or Sheet ID missing.")
            return

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_path, scopes=scopes
            )
            self.client = gspread.authorize(credentials)
            self.sheet = self.client.open_by_key(self.sheet_id).sheet1
            self.ensure_headers()
            logger.info("Successfully connected to Google Sheets.")
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}", exc_info=True)

    def append_row(self, user_id: int, full_name: str, username: str, score: int, is_hot: bool, eval_reasons: str, answers: List[str], link: str):
        """Appends a new row to the sheet with candidate details."""
        if not self.sheet:
            logger.warning("Google Sheets client not initialized. Skipping append.")
            return

        # Format: [Date, Full Name, Username, Profile Link, Score, Is Hot?, Explanation, Link, Q1, Q2, Q3, Q4, Q5]
        row_data = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            full_name,
            f"@{username}" if username else "N/A",
            f"tg://user?id={user_id}",
            str(score),
            "Yes" if is_hot else "No",
            eval_reasons,
            link
        ]
        row_data.extend(answers)

        try:
            self.sheet.append_row(row_data)
            logger.info(f"Successfully appended row for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to append row to Google Sheets: {e}", exc_info=True)

    def ensure_headers(self):
        """Ensures the sheet has the correct header row."""
        if not self.sheet:
            return

        try:
            # Check if first row is empty
            first_row = self.sheet.row_values(1)
            if not first_row:
                headers = ["Date", "Full Name", "Username", "Profile Link", "Score", "Is Hot?", "Explanation", "Link", "Q1", "Q2", "Q3", "Q4", "Q5"]
                self.sheet.insert_row(headers, index=1)
                logger.info("Inserted headers into Google Sheet.")
        except Exception as e:
            logger.error(f"Failed to ensure headers: {e}", exc_info=True)

    def get_stats(self) -> dict:
        """Fetches all data and calculates basic statistics."""
        if not self.sheet:
            return {}

        try:
            all_values = self.sheet.get_all_values()
            if not all_values or len(all_values) < 2:
                return {
                    "total_screened": 0,
                    "avg_score": 0,
                    "top_candidates": []
                }

            headers = all_values[0]
            data_rows = all_values[1:]
            
            # Map rows to dictionaries manually to avoid "duplicate header" errors
            records = []
            for row in data_rows:
                record = {}
                for i, header in enumerate(headers):
                    if header and i < len(row):
                        record[header] = row[i]
                records.append(record)

            total_screened = len(records)
            scores = []
            for r in records:
                try:
                    score_val = r.get("Score")
                    if score_val:
                        scores.append(int(score_val))
                except (ValueError, TypeError):
                    continue
            
            avg_score = sum(scores) / len(scores) if scores else 0

            # Sort by score for top 3
            def get_score(record):
                try:
                    return int(record.get("Score", 0))
                except (ValueError, TypeError):
                    return 0

            sorted_records = sorted(records, key=get_score, reverse=True)
            top_candidates = sorted_records[:3]

            return {
                "total_screened": total_screened,
                "avg_score": round(avg_score, 1),
                "top_candidates": top_candidates
            }
        except Exception as e:
            logger.error(f"Failed to fetch stats from Google Sheets: {e}", exc_info=True)
            return {}
