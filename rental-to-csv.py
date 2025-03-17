import firebase_admin
from firebase_admin import credentials, firestore
import csv
import datetime

def flatten_dict(d, parent_key='', sep='_'):
    """
    Recursively flattens a nested dictionary.
    For example, a key like 'budget' that contains a dictionary
    with keys 'from' and 'to' will become 'budget_from' and 'budget_to'.
    """
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items

def convert_unix_to_readable(ts):
    """
    Converts a Unix timestamp (seconds since epoch) to a readable date format.
    Adjust the format string as needed.
    """
    try:
        return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    except Exception as e:
        return ts  # Return original value if conversion fails

# Initialize Firebase app with your service account key
cred = credentials.Certificate('acn-resale-inventories-dde03-firebase-adminsdk-ikyw4-1d40de00d3.json')  # Update this path as needed!
firebase_admin.initialize_app(cred)

# Initialize Firestore client
db = firestore.client()

# Fetch all documents from the 'rental-inventories' collection
docs = list(db.collection('rental-inventories').stream())

if not docs:
    print("No documents found in the 'rental-inventories' collection.")
else:
    # Define the desired header order exactly as you need it:
    desired_headers = [
        "Property Id", "Property Name", "Property Type", "Plot Size", "SBUA",
        "Rent Per Month in Lakhs", "Maintenance Charges", "Security Deposit", "Configuration",
        "Facing", "Furnishing Status", "Micromarket", "Area", "Available From",
        "Floor Number", "Lease Period", "Lock-in Period", "Amenities", "Extra details",
        "Restrictions", "Veg/Non Veg", "Pet friendly", "Drive Link", "mapLocation",
        "Coordinates", "Date of inventory added", "Date of Status Last Checked",
        "Agent Id", "Agent Number", "Agent Name", "Exact Floor"
    ]
    
    # Map the desired CSV header to the corresponding key in your Firestore data.
    # Update these mappings if your Firestore field names are different.
    mapping = {
        "Property Id": "propertyId",
        "Property Name": "propertyName",
        "Property Type": "propertyType",
        "Plot Size": "plotSize",
        "SBUA": "sbua",
        "Rent Per Month in Lakhs": "rentPerMonthInLakhs",
        "Maintenance Charges": "maintenanceCharges",
        "Security Deposit": "securityDeposit",
        "Configuration": "configuration",
        "Facing": "facing",
        "Furnishing Status": "furnishingStatus",
        "Micromarket": "micromarket",
        "Area": "area",
        "Available From": "availableFrom",
        "Floor Number": "floorNumber",
        "Lease Period": "leasePeriod",
        "Lock-in Period": "lockInPeriod",
        "Amenities": "amenities",
        "Extra details": "extraDetails",
        "Restrictions": "restrictions",
        "Veg/Non Veg": "vegNonVeg",
        "Pet friendly": "petFriendly",
        "Drive Link": "driveLink",
        "mapLocation": "mapLocation",
        "Coordinates": "coordinates",
        "Date of inventory added": "dateOfInventoryAdded",
        "Date of Status Last Checked": "dateOfStatusLastChecked",
        "Agent Id": "agentId",
        "Agent Number": "agentNumber",
        "Agent Name": "agentName",
        "Exact Floor": "exactFloor"
    }
    
    output_rows = []
    
    # Process each document: flatten, convert dates, and map to the desired columns.
    for doc in docs:
        data = doc.to_dict()
        flat_data = flatten_dict(data)
        
        # Convert timestamp fields if they exist and are numeric
        if "dateOfInventoryAdded" in flat_data and isinstance(flat_data["dateOfInventoryAdded"], (int, float)):
            flat_data["dateOfInventoryAdded"] = convert_unix_to_readable(flat_data["dateOfInventoryAdded"])
        if "dateOfStatusLastChecked" in flat_data and isinstance(flat_data["dateOfStatusLastChecked"], (int, float)):
            flat_data["dateOfStatusLastChecked"] = convert_unix_to_readable(flat_data["dateOfStatusLastChecked"])
        
        # Create a row dict for the CSV based on the desired headers and mapping.
        row = {}
        for header in desired_headers:
            firestore_key = mapping.get(header)
            row[header] = flat_data.get(firestore_key, "")
        output_rows.append(row)
    
    # Write the data to a CSV file using the desired header order.
    with open('rentals.csv', mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=desired_headers)
        writer.writeheader()
        for row in output_rows:
            writer.writerow(row)
    
    print("Export completed! Data has been written to 'rentals.csv'.")
