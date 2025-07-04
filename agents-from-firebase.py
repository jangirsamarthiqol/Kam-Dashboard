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

# Ensure UTF-8 output (fixes UnicodeEncodeError on Windows)
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')

# Load environment variables from .env file
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
        docs = list(collection_ref.stream())
        if not docs:
            print("⚠️ No documents found in Firestore.")
            return []
        
        rows = []
        for doc in docs:
            try:
                item = doc.to_dict()
                if not isinstance(item, dict):
                    print(f"⚠️ Unexpected data format in document {doc.id}: {item}")
                    continue

                # Clean and convert existing fields
                item["phonenumber"] = clean_phone_number(item.get("phonenumber", ""))
                item["added"] = convert_unix_to_date(item.get("added"))
                item["lastModified"] = convert_unix_to_date(item.get("lastModified"))

                # New: compute trialEnd based on planExpiry & userType
                plan_expiry = item.get("planExpiry")
                if item.get("userType") in ("trial", "premium") and plan_expiry:
                    item["trialEnd"] = convert_unix_to_date(plan_expiry)
                else:
                    item["expiry"] = convert_unix_to_date(plan_expiry)

                # New: compute nextRenewal based on planExpiry
                if next_renewal := item.get("nextRenewal"):
                    item["nextRenewal"] = convert_unix_to_date(next_renewal)
                else:
                    item["nextRenewal"] = ""

                if "trialUsed" in item and item["trialUsed"]:
                    item["trialStartedAt"] = convert_unix_to_date(item.get("trialStartedAt", ""))

                # Flatten list fields if needed
                processed = {k: flatten_field(v) for k, v in item.items()}
                rows.append(processed)

            except Exception as doc_error:
                print(f"⚠️ Error processing document {doc.id}: {doc_error}")

        print(f"✅ Successfully fetched {len(rows)} records from Firestore.")
        return rows

    except Exception as e:
        print(f"❌ Error fetching data from Firestore: {e}")
        return []

def write_to_google_sheet(data, spreadsheet_id, sheet_name):
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
        
        credentials_obj = Credentials.from_service_account_info(
            sheets_creds,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        gc = gspread.authorize(credentials_obj)
        spreadsheet = gc.open_by_key(spreadsheet_id)
        
        try:
            sheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="50")
            print(f"✅ New sheet '{sheet_name}' created.")
        
        print(f"✅ Google Sheet '{sheet_name}' opened successfully.")
        
        # Define the fixed column order
        fixed_columns = [
            "phonenumber", "cpId", "name", "extraDetails", "verified", "businessName",
            "myInventories", "areaOfOperation", "firmSize", "firmName", "lastModified",
            "notes", "blacklisted", "gstNo", "dailyCredits", "added", "admin", "kam",
            "reraId", "monthlyCredits", "userType", "trialUsed", "trialEnd","nextRenewal","onboardingComplete","expiry","trialUsed","trialStartedAt","areaOfOperation"
        ]
        
        # Ensure all data rows follow the fixed column order
        formatted_data = [
            [item.get(field, "") for field in fixed_columns]
            for item in data
        ]
        
        data_to_write = [fixed_columns] + formatted_data
        sheet.clear()
        sheet.update(values=data_to_write, range_name="A1")
        print("✅ Data written successfully with a fixed column order.")
    except Exception as e:
        print(f"❌ Error writing to Google Sheets: {e}")

def main():
    try:
        initialize_firebase()
        print("🔍 Firebase initialized, moving to Firestore fetch...")
        collection_name = "agents"
        data = fetch_firestore_data(collection_name)
        print("🔍 Firestore fetch completed, checking data...")
        if data:
            spreadsheet_id = "17_9YH7wcHHlgMmBOp50AuYR0Kx0_7-DQMoO38RBI3vg"
            sheet_name = "Sheet1"
            print(f"🔍 Writing {len(data)} records to Google Sheets...")
            write_to_google_sheet(data, spreadsheet_id, sheet_name)
        else:
            print("⚠️ No data to write to Google Sheets.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
