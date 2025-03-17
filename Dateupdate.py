import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Load environment variables from .env file (for Firebase and Sheets credentials)
load_dotenv()

# ---------------------------
# Firebase Initialization using env variables
# ---------------------------
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

def get_firestore_client():
    return firestore.client()

# ---------------------------
# Google Sheets API Initialization using env variables
# ---------------------------
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
        credentials_ = Credentials.from_service_account_info(
            sheets_creds,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        service = build("sheets", "v4", credentials=credentials_)
        print("✅ Google Sheets API initialized successfully.")
        return service
    except Exception as e:
        print(f"❌ Error initializing Google Sheets API: {e}")
        return None

# ---------------------------
# Utility: Convert date string to Unix timestamp
# ---------------------------
def convert_date_to_unix(date_str):
    """
    Converts a date from format 'DD/Mon/YYYY' to a Unix timestamp in seconds
    using the current UTC time.
    """
    try:
        if not date_str or pd.isna(date_str):
            return None
        date_str = str(date_str).strip()
        date_obj = datetime.strptime(date_str, "%d/%b/%Y")
        current_time = datetime.now(timezone.utc).time()
        date_time_obj = datetime.combine(date_obj, current_time).replace(tzinfo=timezone.utc)
        return int(date_time_obj.timestamp())
    except ValueError:
        print(f"Invalid date format: {date_str}")
        return None

# ---------------------------
# Main function: Batch update Firestore with data from Google Sheet
# ---------------------------
def main():
    # Initialize Firebase and Firestore client
    initialize_firebase()
    db = get_firestore_client()

    # Initialize Google Sheets API
    sheets_service = get_sheets_service()
    if not sheets_service:
        return

    # Hardcoded spreadsheet ID, sheet name, and range (Sheet77, columns A to C)
    spreadsheet_id = "14rr4IiEfMVQ_GlzZ-90EkeVNuo4uk_HjjGf8104a3JI"
    range_name = "Sheet77!A:C"
    
    # Fetch data from Google Sheet
    sheet = sheets_service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    
    if not values:
        print("No data found in the Google Sheet.")
        return

    # Assume first row contains headers
    headers = values[0]
    data = values[1:]
    dataframe = pd.DataFrame(data, columns=headers)
    dataframe = dataframe.rename(columns=lambda x: x.strip())  # Trim whitespace from headers

    # Get Firestore collection name from env or use default "ACN123"
    collection_name = os.getenv("FIRESTORE_COLLECTION", "ACN123")
    
    # Retrieve existing document IDs from Firestore
    existing_ids = set()
    for doc in db.collection(collection_name).stream():
        existing_ids.add(doc.id)
    print(f"Found {len(existing_ids)} existing documents in collection '{collection_name}'.")

    # Create a batch to perform multiple updates at once
    batch = db.batch()
    batch_count = 0
    batch_limit = 500  # Firestore batch limit

    # Process each row from the Google Sheet
    for _, row in dataframe.iterrows():
        property_id = row["propertyId"]  # Field name in Google Sheet
        date_str = row["dateOfStatusLastChecked"]  # Field name in Google Sheet
        # Default status is "Available" if not provided
        status = row["status"] if pd.notna(row["status"]) and str(row["status"]).strip() else "Available"
        timestamp = convert_date_to_unix(date_str)

        if timestamp:
            if property_id in existing_ids:
                doc_ref = db.collection(collection_name).document(property_id)
                batch.update(doc_ref, {
                    "dateOfStatusLastChecked": timestamp,
                    "status": status
                })
                batch_count += 1
                # Commit batch when limit is reached
                if batch_count == batch_limit:
                    batch.commit()
                    print(f"Committed a batch of {batch_count} updates.")
                    batch = db.batch()
                    batch_count = 0
            else:
                print(f"Skipping update for {property_id} as it does not exist in Firestore.")
        else:
            print(f"Skipping update for {property_id} due to invalid date.")

    # Commit any remaining updates in the batch
    if batch_count > 0:
        batch.commit()
        print(f"Committed the final batch of {batch_count} updates.")

    print("Update process completed.")

if __name__ == "__main__":
    main()
