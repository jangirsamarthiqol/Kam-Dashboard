import csv
from datetime import datetime
from google.cloud import firestore
from google.oauth2 import service_account

# --- CONFIGURATION ---
SERVICE_ACCOUNT_PATH = "credentials/masalServiceAccountKey.json"  # ← your JSON key
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

    # 3) Gather all field names & convert invoice_date
    fieldnames = set()
    records = []
    for doc in docs:
        data = doc.to_dict()
        data["document_id"] = doc.id

        # ──────────────── CONVERT invoice_date ────────────────
        if "invoice_date" in data and isinstance(data["invoice_date"], datetime):
            # seconds since epoch
            data["invoice_date"] = int(data["invoice_date"].timestamp())
            # if you need milliseconds instead, use:
            # data["invoice_date"] = int(data["invoice_date"].timestamp() * 1000)
        # ────────────────────────────────────────────────────────

        fieldnames.update(data.keys())
        records.append(data)

    fieldnames = sorted(fieldnames)  # deterministic header order

    # 4) Write CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            row = {k: rec.get(k, "") for k in fieldnames}
            writer.writerow(row)

    print(f"✅ Exported {len(records)} documents to `{OUTPUT_CSV}`.")

if __name__ == "__main__":
    export_collection_to_csv()
