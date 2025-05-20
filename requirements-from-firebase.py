import os
import math
import firebase_admin
from firebase_admin import credentials, firestore
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone
from dotenv import load_dotenv
import sys, codecs

# Ensure UTF-8 output
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')

# Load environment variables
load_dotenv()

# ---------------------------
# Firebase Configuration
# ---------------------------
FIREBASE_PROJECT_ID       = os.getenv("FIREBASE_PROJECT_ID")
FIREBASE_PRIVATE_KEY_ID   = os.getenv("FIREBASE_PRIVATE_KEY_ID")
FIREBASE_PRIVATE_KEY      = os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n')
FIREBASE_CLIENT_EMAIL     = os.getenv("FIREBASE_CLIENT_EMAIL")
FIREBASE_CLIENT_ID        = os.getenv("FIREBASE_CLIENT_ID")

# ---------------------------
# Google Sheets Configuration
# ---------------------------
GOOGLE_SHEET_ID = "14rr4IiEfMVQ_GlzZ-90EkeVNuo4uk_HjjGf8104a3JI"
SHEET_NAME      = "requirements-from-firebase"

# ---------------------------
# Firestore Collection Name
# ---------------------------
FIRESTORE_COLLECTION_NAME = os.getenv("FIRESTORE_REQUIREMENTS_COLLECTION_NAME", "requirements")

# ---------------------------
# Initialize Firebase Admin SDK
# ---------------------------
def initialize_firebase():
    try:
        cred_data = {
            "type": "service_account",
            "project_id": FIREBASE_PROJECT_ID,
            "private_key_id": FIREBASE_PRIVATE_KEY_ID,
            "private_key": FIREBASE_PRIVATE_KEY,
            "client_email": FIREBASE_CLIENT_EMAIL,
            "client_id": FIREBASE_CLIENT_ID,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{FIREBASE_CLIENT_EMAIL.replace('@', '%40')}"
        }
        cred = credentials.Certificate(cred_data)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully.")
    except Exception as e:
        print(f"❌ Error initializing Firebase: {e}")

# ---------------------------
# Convert Unix timestamp to readable date
# ---------------------------
def convert_unix_to_date(unix_timestamp):
    try:
        if not unix_timestamp:
            return ""
        return datetime.fromtimestamp(int(unix_timestamp), tz=timezone.utc).strftime('%d/%b/%Y')
    except Exception as e:
        print(f"⚠️ Error converting timestamp {unix_timestamp}: {e}")
        return ""

# ---------------------------
# Sanitize strings (remove leading apostrophes)
# ---------------------------
def sanitize_str(value):
    if isinstance(value, str):
        return value.lstrip("'")
    return str(value)

# ---------------------------
# Fetch data from Firestore requirements collection
# ---------------------------
def fetch_requirements_data(collection_name):
    try:
        db = firestore.client()
        print(f"🔍 Fetching Firestore collection: {collection_name}")
        docs = list(db.collection(collection_name).stream())
        if not docs:
            print("⚠️ No documents found in Firestore.")
            return []

        print(f"📄 Found {len(docs)} documents.")
        rows = []
        for doc in docs:
            try:
                item = doc.to_dict()
                budget = item.get("budget", {}) or {}
                row = [
                    sanitize_str(item.get("requirementId", "")),
                    sanitize_str(item.get("agentCpid", "")),
                    sanitize_str(item.get("propertyName", "")),
                    sanitize_str(item.get("assetType", "")),
                    sanitize_str(item.get("configuration", "")),
                    sanitize_str(convert_unix_to_date(item.get("added"))),
                    sanitize_str(convert_unix_to_date(item.get("lastModified"))),
                    sanitize_str(item.get("area", "")),
                    sanitize_str(budget.get("from", "")),
                    sanitize_str(budget.get("to", "")),
                    sanitize_str(item.get("marketValue", "")),
                    sanitize_str(item.get("requirementDetails", "")),
                    sanitize_str(item.get("status", ""))
                ]
                rows.append(row)
            except Exception as doc_err:
                print(f"⚠️ Error processing document {doc.id}: {doc_err}")
        print(f"✅ Successfully fetched {len(rows)} records.")
        return rows
    except Exception as e:
        print(f"❌ Error fetching data from Firestore: {e}")
        return []

# ---------------------------
# Write data to Google Sheet
# ---------------------------
def write_to_google_sheet(data):
    try:
        if not data:
            print("⚠️ No data to write to Google Sheets.")
            return

        creds_data = {
            "type": "service_account",
            "project_id": os.getenv("GSPREAD_PROJECT_ID"),
            "private_key_id": os.getenv("GSPREAD_PRIVATE_KEY_ID"),
            "private_key": os.getenv("GSPREAD_PRIVATE_KEY", "").replace('\\n', '\n'),
            "client_email": os.getenv("GSPREAD_CLIENT_EMAIL"),
            "client_id": os.getenv("GSPREAD_CLIENT_ID"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.getenv('GSPREAD_CLIENT_EMAIL').replace('@', '%40')}"
        }
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(creds_data, scopes=scopes)
        gc = gspread.authorize(creds)
        print("✅ Google Sheets API authenticated.")

        sheet = gc.open_by_key(GOOGLE_SHEET_ID).worksheet(SHEET_NAME)
        print(f"✅ Opened sheet '{SHEET_NAME}'.")

        headers = [
            "Requirement ID", "Agent CP ID", "Property Name", "Asset Type", "Configuration",
            "Added Date", "Last Modified Date", "Area", "Budget From", "Budget To",
            "Market Value", "Requirement Details", "Status"
        ]
        payload = [headers] + data

        sanitized = []
        for row in payload:
            sanitized_row = [cell if cell != "nan" else "" for cell in row]
            sanitized.append(sanitized_row)

        sheet.clear()
        print("✅ Sheet cleared.")
        # Use USER_ENTERED so dates and numbers are parsed
        sheet.update("A1", sanitized, value_input_option='USER_ENTERED')
        print("✅ Data written successfully.")
    except Exception as e:
        print(f"❌ Error writing to Google Sheets: {e}")

# ---------------------------
# Main
# ---------------------------
def main():
    initialize_firebase()
    data = fetch_requirements_data(FIRESTORE_COLLECTION_NAME)
    if data:
        write_to_google_sheet(data)
    else:
        print("⚠️ No data to write.")

if __name__ == "__main__":
    main()