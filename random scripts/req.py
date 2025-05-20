import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd

# Initialize Firebase Admin SDK
cred = credentials.Certificate("acn-resale-inventories-dde03-firebase-adminsdk-ikyw4-1d40de00d3.json")  # Replace with your key file path
firebase_admin.initialize_app(cred)

# Initialize Firestore client
db = firestore.client()

# Collection name
collection_name = "requirements"

def fetch_firestore_data():
    """Fetch all documents from Firestore collection and return as a list of dictionaries."""
    docs = db.collection(collection_name).stream()
    data = []
    
    for doc in docs:
        doc_data = doc.to_dict()
        doc_data['id'] = doc.id  # Include document ID for reference
        data.append(doc_data)
    
    return data

def save_to_csv(data, filename="requirements.csv"):
    """Save data to a CSV file."""
    if not data:
        print("No data found in Firestore collection.")
        return
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data successfully saved to {filename}")

if __name__ == "__main__":
    firestore_data = fetch_firestore_data()
    save_to_csv(firestore_data)
