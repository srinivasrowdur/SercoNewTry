from google.cloud import storage
from datetime import datetime, timedelta

# Your bucket name
BUCKET_NAME = "sercodemoupload"

def verify_gcs_setup():
    """Verify Google Cloud Storage setup"""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        bucket.reload()
        return True
    except Exception as e:
        print(f"GCS Setup Error: {str(e)}")
        print("\nPlease ensure:")
        print("1. You have installed google-cloud-storage")
        print(f"2. You have access to the bucket: {BUCKET_NAME}")
        print("3. You have authenticated with Google Cloud:")
        print("   Run: gcloud auth application-default login")
        return False

def upload_file(file_content, original_filename):
    """Upload a file to GCS and return the GCS path"""
    try:
        # Generate blob name with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        blob_name = f"audio_uploads/{timestamp}_{original_filename}"
        
        # Upload the file
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)
        
        # Upload the file content
        blob.upload_from_string(
            file_content,
            content_type='audio/mpeg'
        )
        
        # Return the GCS path
        gcs_path = f"gs://{BUCKET_NAME}/{blob_name}"
        print(f"File uploaded successfully to: {gcs_path}")
        return gcs_path
    
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return None

def list_files(prefix="audio_uploads/"):
    """List files in the bucket with given prefix"""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blobs = bucket.list_blobs(prefix=prefix)
        
        files = []
        for blob in blobs:
            files.append({
                'name': blob.name,
                'size': blob.size,
                'updated': blob.updated,
                'url': f"gs://{BUCKET_NAME}/{blob.name}"
            })
        return files
    
    except Exception as e:
        print(f"Error listing files: {str(e)}")
        return []

def get_signed_url(gcs_path):
    """Generate a signed URL for temporary access to the audio file"""
    client = storage.Client()
    bucket_name = gcs_path.split('/')[0]
    blob_name = '/'.join(gcs_path.split('/')[1:])
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.utcnow() + timedelta(minutes=15),
        method="GET"
    )
    return url

# Test the setup
if __name__ == "__main__":
    print(f"Verifying Google Cloud Storage setup for bucket: {BUCKET_NAME}")
    if verify_gcs_setup():
        print(f"✓ Successfully connected to bucket: {BUCKET_NAME}")
        
        # List existing files
        print("\nListing existing files in audio_uploads/:")
        files = list_files()
        if files:
            for file in files:
                print(f"- {file['name']} ({file['size']} bytes)")
        else:
            print("No files found in audio_uploads/")
        
        # Test upload with a small test file
        print("\nTesting file upload...")
        test_content = b"Test audio content"
        test_filename = "test.mp3"
        
        gcs_path = upload_file(test_content, test_filename)
        if gcs_path:
            print(f"✓ Test file uploaded successfully to: {gcs_path}")
        else:
            print("✗ Test file upload failed")
    else:
        print("\n✗ GCS setup verification failed") 