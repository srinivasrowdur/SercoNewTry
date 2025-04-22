import streamlit as st
from agentWorkflow import AudioTranscriptionWorkflow
import os
from pathlib import Path
import requests
from datetime import datetime
import uuid

def generate_unique_filename(original_filename):
    """Generate a unique filename with timestamp and UUID"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    extension = os.path.splitext(original_filename)[1]
    return f"{timestamp}_{unique_id}{extension}"

def upload_to_signed_url(file_content, signed_url):
    """Upload file to Google Cloud Storage using signed URL"""
    try:
        headers = {
            'Content-Type': 'audio/mpeg',
        }
        response = requests.put(signed_url, data=file_content, headers=headers)
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Upload error: {str(e)}")
        return False

def save_uploaded_file(uploaded_file):
    """Save uploaded file to a temporary directory and return the path"""
    try:
        # Create a temporary directory if it doesn't exist
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        unique_filename = generate_unique_filename(uploaded_file.name)
        temp_path = temp_dir / unique_filename
        
        # Save the file
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())
            
        return str(temp_path)
    except Exception as e:
        st.sidebar.error(f"Error saving file: {str(e)}")
        return None

def main():
    # Set page config
    st.set_page_config(
        page_title="Report Generator Agent",
        page_icon="🎙️",
        layout="wide"
    )
    
    # Initialize session state
    if 'transcription' not in st.session_state:
        st.session_state.transcription = None
    if 'conversation_parts' not in st.session_state:
        st.session_state.conversation_parts = []
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'gcs_url' not in st.session_state:
        st.session_state.gcs_url = None
    
    # Main title
    st.title("Report Generator Agent")
    
    # Create tabs first so we can reference them
    tab1, tab2 = st.tabs(["Transcription", "Conversation"])
    
    # Create placeholders in tabs for updates
    with tab1:
        transcription_placeholder = st.empty()
    with tab2:
        conversation_placeholder = st.empty()
    
    # Sidebar for file upload
    with st.sidebar:
        st.header("Upload Recording")
        uploaded_file = st.file_uploader("Choose an MP3 file", type=['mp3'])
        
        # Input field for signed URL
        signed_url = st.text_input("Enter Google Cloud Storage signed URL", 
                                 help="Paste the signed URL for file upload")
        
        if uploaded_file and signed_url:
            st.write("File details:")
            st.write(f"- Filename: {uploaded_file.name}")
            st.write(f"- File size: {uploaded_file.size/1024:.2f} KB")
            
            if st.button("Process Recording"):
                try:
                    # First upload to GCS
                    with st.spinner("Uploading file to Google Cloud Storage..."):
                        upload_success = upload_to_signed_url(
                            uploaded_file.getvalue(), 
                            signed_url
                        )
                        
                        if upload_success:
                            st.success("File uploaded successfully!")
                            st.session_state.gcs_url = signed_url.split('?')[0]  # Base URL without signature
                            
                            # Now process with workflow
                            st.session_state.processing = True
                            st.session_state.transcription = None
                            st.session_state.conversation_parts = []
                            
                            # Save locally for processing
                            file_path = save_uploaded_file(uploaded_file)
                            
                            if file_path:
                                workflow = AudioTranscriptionWorkflow()
                                progress_text = st.empty()
                                
                                progress_text.text("Starting transcription...")
                                for response in workflow.run(message=file_path):
                                    if "Transcription completed" in response.content:
                                        # Store and display raw transcription
                                        transcription = response.content.split("\n\n", 1)[1]
                                        st.session_state.transcription = transcription
                                        transcription_placeholder.text(transcription)
                                        
                                        # Add download button for transcription
                                        with tab1:
                                            st.download_button(
                                                "Download Transcription",
                                                transcription,
                                                file_name="transcription.txt",
                                                mime="text/plain"
                                            )
                                    else:
                                        # Add to conversation
                                        st.session_state.conversation_parts.append(response.content)
                                        formatted_conversation = format_conversation_markdown(
                                            st.session_state.conversation_parts
                                        )
                                        conversation_placeholder.markdown(formatted_conversation)
                                    
                                    progress_text.text(f"Processing: {response.content[:50]}...")
                                
                                progress_text.empty()
                                st.success("Processing completed!")
                                
                                # Cleanup local file
                                try:
                                    os.remove(file_path)
                                except Exception as e:
                                    st.warning(f"Could not remove temporary file: {str(e)}")
                        else:
                            st.error("Failed to upload file to Google Cloud Storage")
                
                except Exception as e:
                    st.error(f"Error during processing: {str(e)}")
                finally:
                    st.session_state.processing = False
        
        elif uploaded_file and not signed_url:
            st.warning("Please enter a signed URL to proceed")
        elif signed_url and not uploaded_file:
            st.warning("Please upload an MP3 file to proceed")
    
    # Display initial content in tabs if not processing
    if not st.session_state.processing:
        # Show GCS URL if available
        if st.session_state.gcs_url:
            st.sidebar.info(f"File stored at: {st.session_state.gcs_url}")
        
        # Transcription tab
        if not st.session_state.transcription:
            transcription_placeholder.info("Upload and process an audio file to see the transcription.")
        
        # Conversation tab
        if not st.session_state.conversation_parts:
            conversation_placeholder.info("Upload and process an audio file to see the conversation.")
        elif st.session_state.conversation_parts:
            formatted_conversation = format_conversation_markdown(
                st.session_state.conversation_parts
            )
            conversation_placeholder.markdown(formatted_conversation)

if __name__ == "__main__":
    main() 