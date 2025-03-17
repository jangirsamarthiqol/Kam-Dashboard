import firebase_admin
from firebase_admin import credentials, firestore
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone
import json
import os
from dotenv import load_dotenv
import sys
import codecs
import pandas as pd

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')

# Load environment variables from .env file
load_dotenv()

# Firebase Admin SDK initialization
def initialize_firebase():
    try:
        if not firebase_admin._apps:  # Prevent re-initialization
            firebase_creds = {
                "type": "service_account",
                "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                "token_uri": "https://oauth2.googleapis.com/token"
            }
            cred = credentials.Certificate(firebase_creds)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized successfully.")
        else:
            print("✅ Firebase already initialized.")
    except Exception as e:
        print(f"❌ Error initializing Firebase: {e}")

# Firestore client
def get_firestore_client():
    return firestore.client()

# Google Sheets API initialization
def get_sheets_service():
    try:
        sheets_creds = {
            "type": "service_account",
            "project_id": os.getenv("GSPREAD_PROJECT_ID"),
            "private_key_id": os.getenv("GSPREAD_PRIVATE_KEY_ID"),
            "private_key": os.getenv("GSPREAD_PRIVATE_KEY").replace("\\n", "\n"),
            "client_email": os.getenv("GSPREAD_CLIENT_EMAIL"),
            "client_id": os.getenv("GSPREAD_CLIENT_ID"),
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        credentials_obj = Credentials.from_service_account_info(sheets_creds, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        return build("sheets", "v4", credentials=credentials_obj)
    except Exception as e:
        print(f"❌ Error initializing Google Sheets API: {e}")
        return None

# Convert Unix timestamps to human-readable dates
def convert_unix_to_date(unix_timestamp):
    try:
        if not unix_timestamp or not isinstance(unix_timestamp, (int, float, str)):
            return ""
        return datetime.fromtimestamp(int(unix_timestamp), tz=timezone.utc).strftime('%Y-%m-%d')
    except Exception as e:
        print(f"⚠️ Error converting timestamp {unix_timestamp}: {e}")
        return ""

# Flatten values for JSON serialization
def flatten_value(value):
    # If the value is NaN, return an empty string (or you can return None if preferred)
    if pd.isna(value):
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value

# Fetch and process Firestore data with sorting
def fetch_firestore_data(collection_name):
    try:
        db = get_firestore_client()
        collection_ref = db.collection(collection_name)
        docs = collection_ref.stream()
        rows = []
        all_fields = set()
        
        for doc in docs:
            item = doc.to_dict()
            item["id"] = doc.id  # Include Firestore Document ID
            item["added"] = convert_unix_to_date(item.get("added"))
            item["lastModified"] = convert_unix_to_date(item.get("lastModified"))
            # Apply flatten_value to each field
            item = {k: flatten_value(v) for k, v in item.items()}
            all_fields.update(item.keys())
            rows.append(item)

        # Sort data in descending order based on 'added' column
        rows.sort(key=lambda x: x.get("added", ""), reverse=True)

        print(f"✅ Successfully fetched {len(rows)} records from Firestore (sorted by 'added').")
        return rows, sorted(all_fields)
    except Exception as e:
        print(f"❌ Error fetching data from Firestore: {e}")
        return [], []

# Write data to Google Sheets
def write_to_google_sheet(data, spreadsheet_id, sheet_name, all_fields):
    try:
        if not data:
            print("⚠️ No data to write to Google Sheets.")
            return
        service = get_sheets_service()
        if not service:
            return
        print(f"✅ Google Sheets API initialized successfully.")
        headers = list(all_fields)
        formatted_data = [[item.get(field, "") for field in headers] for item in data]
        sheet_data = [headers] + formatted_data
        service.spreadsheets().values().clear(spreadsheetId=spreadsheet_id, range=sheet_name).execute()
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=sheet_name,
            valueInputOption="RAW",
            body={"values": sheet_data}
        ).execute()
        print(f"✅ Data written successfully to Google Sheets.")
    except Exception as e:
        print(f"❌ Error writing to Google Sheets: {e}")

# Main function
def main():
    try:
        initialize_firebase()
        print("🔍 Firebase initialized, moving to Firestore fetch...")
        collection_name = "enquiries"
        data, all_fields = fetch_firestore_data(collection_name)
        print("🔍 Firestore fetch completed, checking data...")
        if data:
            spreadsheet_id = "18iYLeUxU6qc5UE7u6OjQ2ZbwSTKeikufQ70fZVa_m3c"
            sheet_name = "Sheet1"
            print(f"🔍 Writing {len(data)} records to Google Sheets...")
            write_to_google_sheet(data, spreadsheet_id, sheet_name, all_fields)
        else:
            print("⚠️ No data to write to Google Sheets.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
