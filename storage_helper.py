from google.cloud import storage
from datetime import datetime, timedelta
import io
import os

# Replace with your actual project and bucket details
PROJECT_ID = "serco-sandbox-landing-01"  # The project ID you set with gcloud
BUCKET_NAME = "sercodemoupload"

def verify_gcs_setup():
    """Verify Google Cloud Storage setup"""
    try:
        storage_client = storage.Client(project=PROJECT_ID)
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

def get_storage_client():
    """Create a storage client with ADC"""
    try:
        return storage.Client(project=PROJECT_ID)
    except Exception as e:
        print(f"Error creating storage client: {str(e)}")
        return None

def upload_file(uploaded_file, filename):
    """Upload a file to Google Cloud Storage"""
    try:
        client = get_storage_client()
        if not client:
            raise Exception("Failed to create storage client")
            
        bucket = client.bucket(BUCKET_NAME)
        
        # Create a unique blob name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        blob_name = f'audio/{timestamp}_{filename}'
        blob = bucket.blob(blob_name)
        
        # Stream the file to GCS
        blob.upload_from_file(
            uploaded_file,
            content_type=uploaded_file.type,
            timeout=600  # 10 minute timeout for large files
        )
        
        print(f"Successfully uploaded to {blob_name}")
        return f'{blob_name}'  # Return just the path, not bucket name
    
    except Exception as e:
        print(f"Upload error details: {str(e)}")
        return None
    finally:
        # Reset file pointer
        uploaded_file.seek(0)

def get_public_url(blob_name):
    """Get the public URL for a blob"""
    return f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}"

def list_files(prefix="audio_uploads/"):
    """List files in the bucket with given prefix"""
    try:
        storage_client = storage.Client(project=PROJECT_ID)
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
    try:
        client = storage.Client(project=PROJECT_ID)
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
    except Exception as e:
        print(f"Signed URL generation error: {str(e)}")
        return None

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