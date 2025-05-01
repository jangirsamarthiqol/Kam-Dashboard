import os
import re
from urllib.parse import urlparse, unquote
from google.oauth2 import service_account
from google.cloud import firestore, storage
from google.api_core.exceptions import GoogleAPIError

# --- CONFIGURATION ---
SERVICE_ACCOUNT_PATH = "masal-db-6cc78-aa35f0672ae1.json"  # ← your JSON key
DOWNLOAD_DIR = "invoices"
COLLECTION_NAME = "Invoices"  # exact, case-sensitive

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def parse_firebase_storage_url(url: str):
    """
    Parse Firebase Storage URL to extract bucket name and object path.
    
    Handles formats like:
    - https://firebasestorage.googleapis.com/v0/b/MY-BUCKET/o/path%2Fto%2Ffile.pdf?alt=media&token=...
    - gs://MY-BUCKET/path/to/file.pdf
    """
    # Check if it's a gs:// URL
    if url.startswith('gs://'):
        parts = url[5:].split('/', 1)
        bucket_name = parts[0]
        object_path = parts[1] if len(parts) > 1 else ''
        return bucket_name, object_path
    
    # Handle HTTP Firebase Storage URL
    p = urlparse(url)
    
    # Standard Firebase Storage URL
    if 'firebasestorage.googleapis.com' in p.netloc:
        path_parts = p.path.split('/')
        
        # Format: /v0/b/BUCKET/o/OBJECT
        if len(path_parts) >= 6 and path_parts[1] == 'v0' and path_parts[2] == 'b' and path_parts[4] == 'o':
            bucket_name = path_parts[3]
            object_path = unquote(path_parts[5])
            return bucket_name, object_path
    
    # If we can't parse it properly, raise an exception
    raise ValueError(f"Unrecognized Firebase Storage URL format: {url}")

def get_extension_from_path(path: str):
    """Extract file extension from path."""
    _, ext = os.path.splitext(path)
    return ext.lower() or ".pdf"  # Default to .pdf if no extension

def sanitize_filename(name: str):
    """Create a safe filename from the given string."""
    # Replace invalid characters with underscores
    name = re.sub(r'[\\/*?:"<>|]', '_', name)
    # Remove leading/trailing whitespace
    return name.strip()

def download_via_storage(client, bucket_name: str, object_path: str, dest_path: str):
    """Download file from Google Cloud Storage."""
    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_path)
        blob.download_to_filename(dest_path)
        print(f"✅ Downloaded via Storage API: {dest_path}")
        return True
    except Exception as e:
        print(f"❌ Storage API error: {e}")
        return False

def main():
    # 1) Init clients
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_PATH
        )
        fs = firestore.Client(credentials=creds, project=creds.project_id)
        stor = storage.Client(credentials=creds, project=creds.project_id)
        print(f"✅ Connected to project: {creds.project_id}")
    except Exception as e:
        print(f"❌ Failed to initialize clients: {e}")
        return

    # 2) Fetch invoices
    try:
        query = fs.collection(COLLECTION_NAME)
        
        # Add the filter if the 'deleted' field exists in your documents
        try:
            docs = list(query.where("deleted", "==", False).stream())
        except:
            # If the filter fails, try without it
            print("⚠️ 'deleted' filter failed, fetching all documents")
            docs = list(query.stream())
            
    except GoogleAPIError as e:
        print(f"❌ Firestore error: {e}")
        return
    
    print(f"📊 Found {len(docs)} documents in collection '{COLLECTION_NAME}'")
    
    if not docs:
        print("⚠️ No docs found. Check your collection name or filter.")
        return

    # 3) Iterate & download
    success_count = 0
    failed_count = 0
    
    for doc in docs:
        data = doc.to_dict()
        doc_id = doc.id
        
        # Try multiple possible field names for the file URL
        url = None
        for field in ["file_url", "fileURL", "fileUrl", "url", "pdfUrl", "downloadUrl", "link"]:
            if field in data and data[field]:
                url = data[field]
                break
                
        # Try to get an invoice number or other identifier
        invoice_id = None
        for field in ["invoice_number", "invoiceNumber", "number", "id", "invoiceId"]:
            if field in data and data[field]:
                invoice_id = data[field]
                break
        
        # Fall back to document ID if no invoice number found
        if not invoice_id:
            invoice_id = doc_id
            
        # Create a clean filename
        safe_id = sanitize_filename(str(invoice_id))
        
        print(f"\n📄 Doc {doc_id} → invoice_id={safe_id!r}")
        
        # Debug: print all fields to help identify URL field
        print(f"   Fields: {', '.join(data.keys())}")
        
        if not url:
            print("   ⚠️ Skipping: no file URL found in document")
            failed_count += 1
            continue
            
        print(f"   URL: {url}")
        
        try:
            # Parse the URL to get bucket and object path
            bucket, obj_path = parse_firebase_storage_url(url)
            
            # Get file extension from the object path
            ext = get_extension_from_path(obj_path)
            
            # Create destination filename
            filename = f"invoice-{safe_id}{ext}"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            
            # Download the file
            if download_via_storage(stor, bucket, obj_path, dest):
                success_count += 1
            else:
                failed_count += 1
                
        except Exception as e:
            print(f"❌ Failed for document {doc_id}: {e}")
            failed_count += 1

    print(f"\n🏁 All done. Downloaded: {success_count}, Failed: {failed_count}")

if __name__ == "__main__":
    main()