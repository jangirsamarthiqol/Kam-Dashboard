import firebase_admin
from firebase_admin import credentials, firestore
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone


# Initialize Firebase Admin SDK
def initialize_firebase():
    try:
        cred = credentials.Certificate("./acn-resale-inventories-dde03-firebase-adminsdk-ikyw4-1d40de00d3.json")  # Path to Firestore service account key
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully.")
    except Exception as e:
        print(f"❌ Error initializing Firebase: {e}")


# Convert Unix timestamp to readable date (DD/Mon/YYYY format)
def convert_unix_to_date(unix_timestamp):
    try:
        if not unix_timestamp or not isinstance(unix_timestamp, (int, float, str)):
            return ""
        return datetime.fromtimestamp(int(unix_timestamp), tz=timezone.utc).strftime('%d/%b/%Y')
    except Exception as e:
        print(f"⚠️ Error converting timestamp {unix_timestamp}: {e}")
        return ""


# Clean phone numbers by removing +91, spaces, and ensuring correct numeric format
def clean_phone_number(number):
    if not number:
        return ""
    
    normalized_number = str(number).replace(" ", "").strip()
    
    if normalized_number.startswith("+91"):
        normalized_number = normalized_number.replace("+91", "").strip()
    
    # Ensure it's numeric but remains a string to preserve formatting
    return int(normalized_number) if normalized_number.isdigit() else normalized_number


# Convert list values to strings (comma-separated)
def flatten_field(value):
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)  # Convert list to comma-separated string
    return value


# Fetch data from Firestore and process it
def fetch_firestore_data(collection_name):
    try:
        db = firestore.client()  # Get Firestore client
        collection_ref = db.collection(collection_name)
        docs = list(collection_ref.stream())  # Convert stream to list

        if not docs:
            print(f"⚠️ No documents found in Firestore collection: {collection_name}")
            return [], []

        all_fields = set()  # Track all possible field names

        # Process each document
        rows = []
        for doc in docs:
            try:
                item = doc.to_dict()
                if not isinstance(item, dict):
                    print(f"⚠️ Unexpected data format in document {doc.id}: {item}")
                    continue

                # Convert timestamps and clean phone numbers
                item["phonenumber"] = clean_phone_number(item.get("phonenumber", ""))
                item["added"] = convert_unix_to_date(item.get("added"))
                item["lastModified"] = convert_unix_to_date(item.get("lastModified"))

                # Convert lists to comma-separated strings
                item = {k: flatten_field(v) for k, v in item.items()}  

                # Track all available fields dynamically
                all_fields.update(item.keys())

                rows.append(item)

            except Exception as doc_error:
                print(f"⚠️ Error processing document {doc.id}: {doc_error}")

        print(f"✅ Successfully fetched {len(rows)} records from Firestore.")
        return rows, sorted(all_fields)  # Return sorted fields for consistency

    except Exception as e:
        print(f"❌ Error fetching data from Firestore: {e}")
        return [], []


# Write data to a specific sheet within a Google Sheets document
def write_to_google_sheet(data, spreadsheet_id, sheet_name, all_fields):
    try:
        if not data:
            print("⚠️ No data to write to Google Sheets.")
            return
        
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        credentials = Credentials.from_service_account_file("enquiry-tracking-1818988a416c.json", scopes=scopes)  # Replace with your Google Sheets API key
        gc = gspread.authorize(credentials)
        print("✅ Google Sheets API authenticated successfully.")
        
        spreadsheet = gc.open_by_key(spreadsheet_id)
        
        # Try to get the sheet by name, otherwise create a new one
        try:
            sheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="50")
            print(f"✅ New sheet '{sheet_name}' created.")

        print(f"✅ Google Sheet '{sheet_name}' opened successfully.")

        # Define the required order for columns
        primary_fields = [
            "phonenumber", "name", "cpId", "verified", "blacklisted",
            "reraId", "firmName", "firmSize", "areaOfOperation", "kam", "added", "lastModified"
        ]

        # Dynamically capture other fields (excluding already included ones)
        additional_fields = [field for field in all_fields if field not in primary_fields]

        # Final column order (Primary fields first, then additional fields)
        final_columns = primary_fields + additional_fields

        # Prepare the data in the correct order
        formatted_data = []
        for item in data:
            formatted_data.append([item.get(field, "") for field in final_columns])

        # Combine headers and data for batch writing
        data_to_write = [final_columns] + formatted_data

        # Fix the DeprecationWarning by using named arguments
        sheet.clear()
        print(f"✅ Sheet '{sheet_name}' cleared successfully.")
        sheet.update(range_name="A1", values=data_to_write)  # Using named arguments to fix DeprecationWarning
        print(f"✅ Data written successfully to Google Sheets in sheet '{sheet_name}'.")

    except Exception as e:
        print(f"❌ Error writing to Google Sheets: {e}")


# Main function
def main():
    try:
        initialize_firebase()
        collection_name = "agents"  # Replace with your Firestore collection name
        data, all_fields = fetch_firestore_data(collection_name)

        if data:
            spreadsheet_id = "17_9YH7wcHHlgMmBOp50AuYR0Kx0_7-DQMoO38RBI3vg"  # Replace with your Google Sheet ID
            sheet_name = "Sheet1"  # Specify the sheet name where you want to write the data
            write_to_google_sheet(data, spreadsheet_id, sheet_name, all_fields)
        else:
            print("⚠️ No data to write to Google Sheets.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    main()
