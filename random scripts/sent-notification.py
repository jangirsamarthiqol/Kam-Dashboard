import firebase_admin
from firebase_admin import credentials, messaging, firestore
from firebase_admin.exceptions import FirebaseError

# 1) Init app once
cred = credentials.Certificate('credentials/acn-resale-inventories-dde03-firebase-adminsdk-ikyw4-1d40de00d3.json')
firebase_admin.initialize_app(cred)

# 2) Firestore client
db = firestore.client()

def get_all_fsm_tokens():
    """
    Returns a list of tuples (doc_ref, token, is_array) for every fsmToken found.
    - is_array=True if the original field was a list, False if it was a single string.
    """
    results = []
    agents = db.collection('agents').stream()
    for doc in agents:
        data = doc.to_dict()
        raw = data.get('fsmToken')
        doc_ref = doc.reference

        if isinstance(raw, str) and raw.strip():
            # single string token
            results.append((doc_ref, raw.strip(), False))
        elif isinstance(raw, (list, tuple)):
            # multiple tokens in an array
            for t in raw:
                if isinstance(t, str) and t.strip():
                    results.append((doc_ref, t.strip(), True))
        # else: skip missing / invalid types

    return results

def send_and_prune_tokens():
    pairs = get_all_fsm_tokens()
    print(f"Found {len(pairs)} token entries, attempting sends…")

    for doc_ref, token, is_array in pairs:
        msg = messaging.Message(
            token=token,
            notification=messaging.Notification(
                title='🔔 Deal Maker Alert',
                body='‘Make every click count.’ Browse listings, engage leads, and close deals fast.'
            )
        )
        try:
            resp = messaging.send(msg)
            print(f'✅ Sent to {token[:8]}…: {resp}')

        except FirebaseError as e:
            code = getattr(e, 'code', '')
            # if it's the “token not registered / not found” family of errors:
            if 'registration-token' in code or code == 'NOT_FOUND':
                if is_array:
                    # remove just this token from the array
                    doc_ref.update({
                        'fsmToken': firestore.ArrayRemove([token])
                    })
                    print(f'🗑 Removed expired token {token[:8]}… from array in {doc_ref.id}')
                else:
                    # it was a single string—delete the whole field
                    doc_ref.update({
                        'fsmToken': firestore.DELETE_FIELD
                    })
                    print(f'🗑 Deleted fsmToken field from {doc_ref.id}')
            else:
                # some other FCM error—log and move on
                print(f'⚠️ Skipped {token[:8]}… — {code}: {e}')

        except Exception as e:
            # catch-all so nothing stalls the loop
            print(f'❌ Unexpected error sending to {token[:8]}… — {e}')


if __name__ == '__main__':
    send_and_prune_tokens()
