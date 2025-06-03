import streamlit as st
import google.genai as genai
from pathlib import Path
import os
from datetime import datetime
import uuid
import tempfile

def generate_unique_filename(original_filename):
    """Generate a unique filename with timestamp and UUID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    extension = os.path.splitext(original_filename)[1]
    return f"{timestamp}_{unique_id}{extension}"

def process_audio_with_genai(uploaded_file):
    """Process audio using Google GenAI client for better large file handling"""
    try:
        # Create a temporary file for the upload
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(uploaded_file.getbuffer())
            temp_file_path = temp_file.name
        
        # Initialize the GenAI client
        client = genai.Client()
        
        # Upload file to Google's servers
        st.info("Uploading file to Google's servers for processing...")
        myfile = client.files.upload(file=temp_file_path)
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        return myfile, client
        
    except Exception as e:
        # Clean up temp file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise e

def generate_transcription(client, file_ref):
    """Generate transcription using the uploaded file reference"""
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=["Transcribe this audio file exactly as spoken.", file_ref]
    )
    return response.text

def generate_conversation(client, transcription_text):
    """Generate formatted conversation from transcription"""
    prompt = f"""Format this transcript as a clean conversation:
    {transcription_text}
    
    Format rules:
    1. Format the transcript as a clean conversation
    2. Use **Speaker:** format for names
    3. Add line breaks between speakers
    4. Keep medical terms exact
    5. Output only the formatted conversation
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[prompt]
    )
    return response.text

def generate_summary_report(client, transcription_text):
    """Generate medical summary report from transcription"""
    prompt = f"""Create a detailed medical summary report from this conversation:
    {transcription_text}
    
    Format the report with these sections using markdown:
    1. ### Patient Information
       - Name
       - Relevant demographic information
    
    2. ### Chief Complaint
       - Main reason for visit
       - Duration of symptoms
    
    3. ### History of Present Illness
       - Onset and progression
       - Previous treatments
       - Current symptoms
    
    4. ### Past Medical History
       - Previous diagnoses
       - Previous treatments
       - Relevant medical history
    
    5. ### Current Medications
       - List all medications mentioned
       - Dosages if specified
    
    6. ### Treatment Plan
       - Current plan
       - Follow-up instructions
       - Medications prescribed
    
    7. ### Assessment
       - Key findings
       - Current status
       - Areas of concern

    Use bullet points for easy reading and maintain medical terminology exactly as mentioned.
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[prompt]
    )
    return response.text

# Initialize session state
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = []
if 'transcription_result' not in st.session_state:
    st.session_state.transcription_result = None
if 'conversation_result' not in st.session_state:
    st.session_state.conversation_result = None
if 'summary_result' not in st.session_state:
    st.session_state.summary_result = None

st.set_page_config(page_title="Report Generator Agent", layout="wide")
st.title("Report Generator Agent")

# File uploader in sidebar
with st.sidebar:
    st.header("Upload Recording")
    uploaded_file = st.file_uploader("Choose an MP3 file", type=['mp3'])
    if uploaded_file:
        st.audio(uploaded_file)
        
        # Show file info
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        st.info(f"File size: {file_size_mb:.1f} MB")
        
        if file_size_mb > 100:
            st.warning("⚠️ Large file detected. Using optimized processing for better performance.")
        
        process_button = st.button("Process Recording", type="primary")
        
        # Display list of processed files
        if st.session_state.processed_files:
            st.markdown("### Previously Processed Files")
            for file_info in st.session_state.processed_files:
                st.text(file_info)

# Main content area with tabs
tab1, tab2, tab3 = st.tabs(["Transcription", "Conversation", "Summary Report"])

if uploaded_file and process_button:
    try:
        # Process with Google GenAI for better large file handling
        file_ref, client = process_audio_with_genai(uploaded_file)
        
        # Transcription
        with tab1:
            st.markdown("### Transcription")
            with st.spinner("Generating transcription..."):
                transcription_text = generate_transcription(client, file_ref)
                st.session_state.transcription_result = transcription_text
                st.markdown(transcription_text)
                
                # Download button
                st.download_button(
                    label="📄 Download Transcription",
                    data=transcription_text,
                    file_name=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key="download_transcription"
                )
        
        # Conversation formatting
        with tab2:
            st.markdown("### Conversation")
            with st.spinner("Formatting conversation..."):
                conversation_text = generate_conversation(client, transcription_text)
                st.session_state.conversation_result = conversation_text
                st.markdown(conversation_text)
                
                # Download button
                st.download_button(
                    label="💬 Download Conversation",
                    data=conversation_text,
                    file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    key="download_conversation"
                )

        # Summary Report
        with tab3:
            st.markdown("### Summary Report")
            with st.spinner("Generating summary report..."):
                summary_text = generate_summary_report(client, transcription_text)
                st.session_state.summary_result = summary_text
                st.markdown(summary_text)
                
                # Download button
                st.download_button(
                    label="📋 Download Summary Report",
                    data=summary_text,
                    file_name=f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    key="download_summary"
                )
        
        # Add to processed files list
        file_info = f"{uploaded_file.name} ({file_size_mb:.1f} MB) - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        if file_info not in st.session_state.processed_files:
            st.session_state.processed_files.append(file_info)
            
        st.success("✅ Processing completed successfully!")
        
    except Exception as e:
        st.error(f"❌ An error occurred while processing the audio file: {str(e)}")
        st.error("Please try again or contact support if the issue persists.")

# Display cached results in tabs even when not processing
else:
    with tab1:
        st.markdown("### Transcription")
        if st.session_state.transcription_result:
            st.markdown(st.session_state.transcription_result)
            st.download_button(
                label="📄 Download Transcription",
                data=st.session_state.transcription_result,
                file_name=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key="cached_download_transcription"
            )
        else:
            st.info("Upload an audio file and click 'Process Recording' to see transcription results here.")
    
    with tab2:
        st.markdown("### Conversation")
        if st.session_state.conversation_result:
            st.markdown(st.session_state.conversation_result)
            st.download_button(
                label="💬 Download Conversation",
                data=st.session_state.conversation_result,
                file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                key="cached_download_conversation"
            )
        else:
            st.info("Upload an audio file and click 'Process Recording' to see conversation results here.")
    
    with tab3:
        st.markdown("### Summary Report")
        if st.session_state.summary_result:
            st.markdown(st.session_state.summary_result)
            st.download_button(
                label="📋 Download Summary Report",
                data=st.session_state.summary_result,
                file_name=f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                key="cached_download_summary"
            )
        else:
            st.info("Upload an audio file and click 'Process Recording' to see summary results here.") 