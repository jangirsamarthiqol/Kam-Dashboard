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
        return ts  # In case of an error, return the original value

# Initialize Firebase app with your service account key
cred = credentials.Certificate('acn-resale-inventories-dde03-firebase-adminsdk-ikyw4-1d40de00d3.json')  # Update this path!
firebase_admin.initialize_app(cred)

# Initialize Firestore client
db = firestore.client()

# Fetch all documents from the 'requirements' collection
docs = list(db.collection('requirements').stream())

if not docs:
    print("No documents found in the 'requirements' collection.")
else:
    flat_docs = []
    all_keys = set()
    
    # Process each document: flatten nested dictionaries and collect keys for the CSV header
    for doc in docs:
        data = doc.to_dict()
        flat_data = flatten_dict(data)
        
        # Convert the 'added' field if it's present and is a number
        if 'added' in flat_data and isinstance(flat_data['added'], (int, float)):
            flat_data['added'] = convert_unix_to_readable(flat_data['added'])
        
        flat_docs.append(flat_data)
        all_keys.update(flat_data.keys())
    
    # Create a sorted list of headers (you can customize the order if needed)
    headers = sorted(all_keys)
    
    # Write the flattened data to a CSV file
    with open('requirements.csv', mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        for flat_data in flat_docs:
            writer.writerow(flat_data)
    
    print("Export completed! Data has been written to 'requirements.csv'.")
