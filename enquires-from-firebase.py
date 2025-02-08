import firebase_admin
from firebase_admin import credentials, firestore
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone
import json  # For converting nested objects to JSON strings

# Firebase Admin SDK initialization
firebase_cred = credentials.Certificate("acn-resale-inventories-dde03-firebase-adminsdk-ikyw4-1d40de00d3.json")
firebase_admin.initialize_app(firebase_cred)

db = firestore.client()

# Google Sheets API initialization
SHEET_ID = "18iYLeUxU6qc5UE7u6OjQ2ZbwSTKeikufQ70fZVa_m3c"  # Replace with your Google Sheet ID
SHEET_NAME = "Sheet1"  # Name of the sheet/tab inside the spreadsheet
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
google_cred = Credentials.from_service_account_file("enquiry-tracking-1818988a416c.json", scopes=SCOPES)
service = build("sheets", "v4", credentials=google_cred)

# Reference to the 'enquiries' collection in Firebase
enquiries_ref = db.collection("enquiries")

def flatten_value(value):
    """
    Convert nested structures (dict, list) into a string representation.
    """
    if isinstance(value, dict) or isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)  # Convert to JSON string for better readability
    return value  # Return as-is if it's a normal value

def fetch_and_update_google_sheet():
    # Fetch all documents from Firestore
    docs = enquiries_ref.stream()
    
    # Convert documents to a list of dictionaries
    enquiries = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id  # Include Firestore Document ID
        
        # Convert Unix timestamps to human-readable dates
        if "added" in data and isinstance(data["added"], (int, float)):
            data["added"] = datetime.fromtimestamp(data["added"], timezone.utc).strftime('%Y-%m-%d')
        if "lastModified" in data and isinstance(data["lastModified"], (int, float)):
            data["lastModified"] = datetime.fromtimestamp(data["lastModified"], timezone.utc).strftime('%Y-%m-%d')
        
        # Flatten any nested objects before adding to the list
        flattened_data = {key: flatten_value(value) for key, value in data.items()}
        enquiries.append(flattened_data)
    
    if not enquiries:
        print("No enquiries found.")
        return
    
    # Get all field names dynamically
    fieldnames = sorted({key for enquiry in enquiries for key in enquiry.keys()})

    # Prepare data for Google Sheets (convert dictionaries to a list of lists)
    sheet_data = [fieldnames]  # First row = headers
    for enquiry in enquiries:
        sheet_data.append([enquiry.get(field, "") for field in fieldnames])
    
    # Clear existing data in the sheet
    service.spreadsheets().values().clear(
        spreadsheetId=SHEET_ID,
        range=SHEET_NAME
    ).execute()
    
    # Write new data to the Google Sheet
    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=SHEET_NAME,
        valueInputOption="RAW",
        body={"values": sheet_data}
    ).execute()

    print("Enquiries updated in Google Sheets")

# Run the function
fetch_and_update_google_sheet()
