import csv
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin SDK
cred = credentials.Certificate('credentials/acn-resale-inventories-dde03-firebase-adminsdk-ikyw4-1d40de00d3.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

def update_kam_for_agents(csv_path):
    # Read CSV into a dict: cpId -> kam
    updates = {}
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cp_id = row['cpId'].strip()
            kam_id = row['kam'].strip()
            updates[cp_id] = kam_id

    # Step 1: Update agents collection kam field
    for cp_id, new_kam in updates.items():
        agents_ref = db.collection('agents')
        # Query agent doc with cpId
        query = agents_ref.where('cpId', '==', cp_id).limit(1).stream()
        agent_doc = None
        for doc in query:
            agent_doc = doc
            break
        if agent_doc:
            # Update kam field
            agent_doc.reference.update({'kam': new_kam})
            print(f'Updated kam for agent {cp_id} to {new_kam}')
        else:
            print(f'Agent with cpId {cp_id} not found')

    # Step 2: Remove cpId from all myAgents arrays in kam collection
    kam_ref = db.collection('kam')
    # Get all kam documents
    all_kam_docs = kam_ref.stream()
    for kam_doc in all_kam_docs:
        doc_ref = kam_doc.reference
        data = kam_doc.to_dict()
        if 'myAgents' in data:
            my_agents = data['myAgents']
            # Find all cpIds to remove from this document's myAgents array
            to_remove = [cp for cp in updates.keys() if cp in my_agents]
            if to_remove:
                # Remove them
                updated_agents = [agent for agent in my_agents if agent not in to_remove]
                doc_ref.update({'myAgents': updated_agents})
                print(f'Removed {to_remove} from kam doc {kam_doc.id}')

    # Step 3: Add cpId to the new kam's myAgents array
    for cp_id, new_kam in updates.items():
        kam_doc_ref = kam_ref.document(new_kam)
        kam_doc = kam_doc_ref.get()
        if kam_doc.exists:
            data = kam_doc.to_dict()
            my_agents = data.get('myAgents', [])
            if cp_id not in my_agents:
                my_agents.append(cp_id)
                kam_doc_ref.update({'myAgents': my_agents})
                print(f'Added {cp_id} to myAgents of kam {new_kam}')
        else:
            # If the kam doc doesn't exist, optionally create it
            kam_doc_ref.set({'myAgents': [cp_id]})
            print(f'Created kam doc {new_kam} and added {cp_id}')

if __name__ == '__main__':
    csv_path = 'random scripts/Untitled spreadsheet - Sheet1 (6).csv'
    update_kam_for_agents(csv_path)
