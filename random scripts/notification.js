// sent-notification.js

const admin = require('firebase-admin');

// 1) Init app once with your service account
const serviceAccount = require('./acn-resale-inventories-dde03-firebase-adminsdk-ikyw4-1d40de00d3.json');
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

async function getAllFsmTokens() {
  /**
   * Fetches every fsmToken (string or array) from the 'agents' collection
   * Returns an array of objects: { docRef, token, isArray }
   */
  const results = [];
  const snapshot = await db.collection('agents').get();

  snapshot.forEach(doc => {
    const data = doc.data();
    const raw = data.fsmToken;
    const docRef = doc.ref;

    if (typeof raw === 'string' && raw.trim()) {
      results.push({ docRef, token: raw.trim(), isArray: false });
    } else if (Array.isArray(raw)) {
      raw.forEach(t => {
        if (typeof t === 'string' && t.trim()) {
          results.push({ docRef, token: t.trim(), isArray: true });
        }
      });
    }
    // skip anything else
  });

  return results;
}

async function sendAndPruneTokens() {
  const pairs = await getAllFsmTokens();f
  console.log(`Found ${pairs.length} token entries, attempting sends…`);

  for (const { docRef, token, isArray } of pairs) {
    try {
      const response = await admin.messaging().send({
        token,
        notification: {
          title: 'Basic Notification',
          body: 'This is a basic notification sent from the server!'
        }
      });
      console.log(`✅ Sent to ${token.slice(0,8)}…: ${response}`);

    } catch (err) {
      const code = err.code || '';

      // prune on “not-registered” or “invalid-registration-token”
      if (
        code.includes('registration-token-not-registered') ||
        code.includes('invalid-registration-token') ||
        code === 'messaging/registration-token-not-registered'
      ) {
        if (isArray) {
          await docRef.update({
            fsmToken: admin.firestore.FieldValue.arrayRemove(token)
          });
          console.log(`🗑 Removed expired token ${token.slice(0,8)}… from array in ${docRef.id}`);
        } else {
          await docRef.update({
            fsmToken: admin.firestore.FieldValue.delete()
          });
          console.log(`🗑 Deleted fsmToken field from ${docRef.id}`);
        }
      } else {
        console.log(`⚠️ Skipped ${token.slice(0,8)}… — ${code}: ${err.message || err}`);
      }
    }
  }
}

sendAndPruneTokens().catch(console.error);
