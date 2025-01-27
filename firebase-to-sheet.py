import firebase_admin
from firebase_admin import credentials, firestore
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone


# Initialize Firebase Admin SDK
def initialize_firebase():
    try:
        cred = credentials.Certificate("./acn-resale-inventories-dde03-firebase-adminsdk-ikyw4-1d40de00d3.json")  # Path to your Firestore service account key
        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully.")
    except Exception as e:
        print(f"Error initializing Firebase: {e}")


# Fetch data from Firestore
def fetch_firestore_data(collection_name):
    try:
        db = firestore.client()  # Get Firestore client
        collection_ref = db.collection(collection_name)
        docs = collection_ref.stream()

        rows = []
        for doc in docs:
            item = doc.to_dict()  # Convert Firestore document to dictionary
            row = [
                item.get("propertyId", ""),
                item.get("cpCode", ""),
                item.get("nameOfTheProperty", ""),
                item.get("assetType", ""),
                item.get("subType", ""),
                item.get("plotSize", ""),
                item.get("carpet", ""),
                item.get("sbua", ""),
                item.get("facing", ""),
                item.get("totalAskPrice", ""),
                item.get("askPricePerSqft", ""),
                item.get("unitType", ""),
                item.get("micromarket", ""),
                item.get("extraDetails", ""),
                item.get("floorNo", ""),
                item.get("handoverDate", ""),
                item.get("area", ""),
                item.get("mapLocation", ""),
                convert_unix_to_date(item.get("dateOfInventoryAdded")),
                convert_unix_to_date(item.get("dateOfStatusLastChecked")),
                item.get("driveLink", ""),
                item.get("buildingKhata", ""),
                item.get("landKhata", ""),
                item.get("buildingAge", ""),
                item.get("ageOfInventory", ""),
                item.get("ageOfStatus", ""),
                item.get("status", ""),
                item.get("tenanted", ""),
                item.get("ocReceived", ""),
                item.get("currentStatus", ""),
                f"{item.get('_geoloc', {}).get('lat', '')}, {item.get('_geoloc', {}).get('lng', '')}",
                item.get("exclusive", ""),
                item.get("exactFloor", ""),
                item.get("eKhata", ""),
                ", ".join(item.get("document", [])) if isinstance(item.get("document"), list) else item.get("document", "")
            ]
            rows.append(row)

        return rows

    except Exception as e:
        print(f"Error fetching data from Firestore: {e}")
        return []


# Convert Unix timestamp to readable date in the format: "16/Jan/2025"
def convert_unix_to_date(unix_timestamp):
    if not unix_timestamp:
        return ""
    return datetime.fromtimestamp(int(unix_timestamp), tz=timezone.utc).strftime('%d/%b/%Y')


# Write data to Google Sheets in batch
def write_to_google_sheet(data, spreadsheet_id):
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        credentials = Credentials.from_service_account_file("enquiry-tracking-1818988a416c.json", scopes=scopes)
        gc = gspread.authorize(credentials)
        print("Google Sheets API authenticated successfully.")
        
        sheet = gc.open_by_key(spreadsheet_id).sheet1
        print("Google Sheet opened successfully.")

        headers = [
            "Property ID", "CP Code", "Name of The property", "Asset Type", "Sub Type",
            "Plot Size", "Carpet (Sq Ft)", "SBUA (Sq ft)", "Facing", "Total Ask Price (Lacs)",
            "Ask Price / Sqft", "Unit Type", "Micromarket", "Extra Details", "Floor No.",
            "Handover Date", "Area", "Map Location", "Date of inventory added", "Date of status last checked",
            "Drive link for more info", "Building Khata", "Land Khata", "Building Age",
            "Age of Inventory", "Age of Status", "Status", "Tenanted or Not",
            "OC Received or not", "Current Status", "Coordinates", "Exclusive", "Exact Floor",
            "eKhata", "Document"
        ]
        
        # Combine headers and data for batch writing
        data_to_write = [headers] + data
        
        # Clear the sheet and write data in a single call
        sheet.clear()
        print("Sheet cleared successfully.")
        sheet.update("A1", data_to_write)
        print("Data written successfully to Google Sheets in batch.")

    except Exception as e:
        print(f"Error writing to Google Sheets: {e}")


# Main function
def main():
    try:
        initialize_firebase()
        collection_name = "ACN123"
        data = fetch_firestore_data(collection_name)

        if data:
            spreadsheet_id = "1o6KI4tXt5yfIOHYQ9JH9RI1NK35DKrJRPHNf0srDnuo"  # Replace with your Google Sheet ID
            write_to_google_sheet(data, spreadsheet_id)
        else:
            print("No data to write to Google Sheets.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
