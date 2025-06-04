import csv
import firebase_admin
from firebase_admin import credentials, firestore

def flatten_dict(d, parent_key='', sep='.'):
    """
    Flatten nested dict into single level with dot notation keys.
    Example: {'a': {'b': 1}} -> {'a.b': 1}
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

# Initialize Firebase Admin SDK
cred = credentials.Certificate('credentials/acn-resale-inventories-dde03-firebase-adminsdk-ikyw4-1d40de00d3.json')
firebase_admin.initialize_app(cred, {
    'projectId': 'acn-resale-inventories-dde03',
})

db = firestore.client()

def fetch_and_export_all_to_csv(output_csv='payments_full.csv'):
    collection_name = 'payments'
    docs = db.collection(collection_name).stream()

    all_rows = []
    all_keys = set()

    # Fetch and flatten each doc
    for doc in docs:
        data = doc.to_dict()
        flat_data = flatten_dict(data)
        all_rows.append(flat_data)
        all_keys.update(flat_data.keys())

    # Sort keys for consistent column order
    header = sorted(all_keys)

    with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in all_rows:
            # Write row, missing keys will be empty
            writer.writerow(row)

    print(f"Exported full payment documents from '{collection_name}' to '{output_csv}'.")

if __name__ == "__main__":
    fetch_and_export_all_to_csv()
