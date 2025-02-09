import firebase_admin
from firebase_admin import credentials, firestore
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone
import json
import os
from dotenv import load_dotenv
import sys
import codecs

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')

# Load environment variables
load_dotenv()

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

def convert_unix_to_date(unix_timestamp):
    try:
        if not unix_timestamp or not isinstance(unix_timestamp, (int, float, str)):
            return ""
        return datetime.fromtimestamp(int(unix_timestamp), tz=timezone.utc).strftime('%d/%b/%Y')
    except Exception as e:
        print(f"⚠️ Error converting timestamp {unix_timestamp}: {e}")
        return ""

def clean_phone_number(number):
    if not number:
        return ""
    normalized_number = str(number).replace(" ", "").strip()
    if normalized_number.startswith("+91"):
        normalized_number = normalized_number.replace("+91", "").strip()
    return int(normalized_number) if normalized_number.isdigit() else normalized_number

def flatten_field(value):
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return value

def fetch_firestore_data(collection_name):
    try:
        db = firestore.client()
        collection_ref = db.collection(collection_name)
        print(f"🔍 Fetching data from Firestore collection: {collection_name}...")

        rows = []
        all_fields = set()
        docs = collection_ref.stream()  # Efficient streaming

        for doc in docs:
            try:
                item = doc.to_dict()
                if not isinstance(item, dict):
                    print(f"⚠️ Unexpected data format in document {doc.id}: {item}")
                    continue
                item["phonenumber"] = clean_phone_number(item.get("phonenumber", ""))
                item["added"] = convert_unix_to_date(item.get("added"))
                item["lastModified"] = convert_unix_to_date(item.get("lastModified"))
                item = {k: flatten_field(v) for k, v in item.items()}
                all_fields.update(item.keys())
                rows.append(item)
            except Exception as doc_error:
                print(f"⚠️ Error processing document {doc.id}: {doc_error}")

        print(f"✅ Successfully fetched {len(rows)} records from Firestore.")
        return rows, list(all_fields)  # Keeping order as per Firestore structure
    except Exception as e:
        print(f"❌ Error fetching data from Firestore: {e}")
        return [], []

def write_to_google_sheet(data, spreadsheet_id, sheet_name, all_fields):
    try:
        if not data:
            print("⚠️ No data to write to Google Sheets.")
            return
        
        sheets_creds = {
            "type": "service_account",
            "project_id": os.getenv("GSPREAD_PROJECT_ID"),
            "private_key_id": os.getenv("GSPREAD_PRIVATE_KEY_ID"),
            "private_key": os.getenv("GSPREAD_PRIVATE_KEY").replace("\\n", "\n"),
            "client_email": os.getenv("GSPREAD_CLIENT_EMAIL"),
            "client_id": os.getenv("GSPREAD_CLIENT_ID"),
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        
        credentials = Credentials.from_service_account_info(sheets_creds, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        gc = gspread.authorize(credentials)
        spreadsheet = gc.open_by_key(spreadsheet_id)

        try:
            sheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="50")
            print(f"✅ New sheet '{sheet_name}' created.")

        print(f"✅ Google Sheet '{sheet_name}' opened successfully.")
        
        # Ensure "phonenumber" is the first column, "cpId" is the second, and preserve the rest of the fields in original Firestore order
        predefined_order = ["phonenumber", "cpId"]
        remaining_fields = [field for field in all_fields if field not in predefined_order]
        headers = predefined_order + remaining_fields

        # Arrange data to match the headers order
        formatted_data = [[item.get(field, "") for field in headers] for item in data]

        sheet.clear()
        sheet.update("A1", [headers] + formatted_data)
        print(f"✅ Data written successfully to Google Sheets with 'phonenumber' as the first column and 'cpId' as the second column.")
    except Exception as e:
        print(f"❌ Error writing to Google Sheets: {e}")

def main():
    try:
        initialize_firebase()
        print("🔍 Firebase initialized, moving to Firestore fetch...")
        
        collection_name = "agents"
        data, all_fields = fetch_firestore_data(collection_name)
        
        print("🔍 Firestore fetch completed, checking data...")
        
        if data:
            spreadsheet_id = "17_9YH7wcHHlgMmBOp50AuYR0Kx0_7-DQMoO38RBI3vg"  # Keep hardcoded if needed
            sheet_name = "Sheet1"
            print(f"🔍 Writing {len(data)} records to Google Sheets...")
            write_to_google_sheet(data, spreadsheet_id, sheet_name, all_fields)
        else:
            print("⚠️ No data to write to Google Sheets.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
