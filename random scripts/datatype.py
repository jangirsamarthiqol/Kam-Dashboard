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
    """Fetch all documents from Firestore collection and return data and data types."""
    docs = db.collection(collection_name).stream()
    
    data = []
    data_types = []

    for doc in docs:
        doc_data = doc.to_dict()
        doc_data['id'] = doc.id  # Include document ID for reference
        
        # Create a dictionary for data types
        doc_types = {key: type(value).__name__ for key, value in doc_data.items()}
        
        data.append(doc_data)
        data_types.append(doc_types)
    
    return data, data_types

def save_to_csv(data, data_types, filename="requirements_with_types.csv"):
    """Save data and data types to a CSV file."""
    if not data:
        print("No data found in Firestore collection.")
        return
    
    # Create DataFrames
    df_data = pd.DataFrame(data)
    df_types = pd.DataFrame(data_types)
    
    # Append " (Type)" to the column names in the types DataFrame
    df_types.columns = [f"{col} (Type)" for col in df_types.columns]

    # Concatenate actual data and types
    df_final = pd.concat([df_data, df_types], axis=1)

    # Save to CSV
    df_final.to_csv(filename, index=False)
    print(f"Data with types successfully saved to {filename}")

if __name__ == "__main__":
    firestore_data, firestore_data_types = fetch_firestore_data()
    save_to_csv(firestore_data, firestore_data_types)
