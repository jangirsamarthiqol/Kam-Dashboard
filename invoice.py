import csv
from google.cloud import firestore
from google.oauth2 import service_account

# --- CONFIGURATION ---
SERVICE_ACCOUNT_PATH = "masalServiceAccountKey.json"  # ← your JSON key
COLLECTION_NAME      = "Invoices"                       # exact, case-sensitive
OUTPUT_CSV           = "invoices.csv"

def export_collection_to_csv():
    # 1) Auth + Firestore client
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_PATH
    )
    db = firestore.Client(credentials=creds, project=creds.project_id)

    # 2) Fetch all docs
    docs = list(db.collection(COLLECTION_NAME).stream())
    if not docs:
        print(f"⚠️ No documents found in `{COLLECTION_NAME}`.")
        return

    # 3) Gather all field names
    fieldnames = set()
    records = []
    for doc in docs:
        data = doc.to_dict()
        data["document_id"] = doc.id               # include the Firestore ID
        fieldnames.update(data.keys())
        records.append(data)

    fieldnames = sorted(fieldnames)                # deterministic header order

    # 4) Write CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            # ensure every column exists
            row = {k: rec.get(k, "") for k in fieldnames}
            writer.writerow(row)

    print(f"✅ Exported {len(records)} documents to `{OUTPUT_CSV}`.")

if __name__ == "__main__":
    export_collection_to_csv()
