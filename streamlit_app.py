import streamlit as st
import google.genai as genai
from pathlib import Path
import os
from datetime import datetime
import uuid
import tempfile
import math
from pydub import AudioSegment

def generate_unique_filename(original_filename):
    """Generate a unique filename with timestamp and UUID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    extension = os.path.splitext(original_filename)[1]
    return f"{timestamp}_{unique_id}{extension}"

def get_audio_duration(file_path):
    """Get audio duration in minutes"""
    try:
        audio = AudioSegment.from_mp3(file_path)
        duration_seconds = len(audio) / 1000
        duration_minutes = duration_seconds / 60
        return duration_minutes
    except Exception as e:
        st.error(f"Error reading audio file: {str(e)}")
        return 0

def chunk_audio_file(file_path, chunk_duration_minutes=20):
    """
    Split audio file into chunks to handle large files
    Returns list of chunk file paths
    """
    try:
        audio = AudioSegment.from_mp3(file_path)
        total_duration_ms = len(audio)
        chunk_duration_ms = chunk_duration_minutes * 60 * 1000  # Convert to milliseconds
        
        chunks = []
        chunk_files = []
        
        # Calculate number of chunks needed
        num_chunks = math.ceil(total_duration_ms / chunk_duration_ms)
        
        for i in range(num_chunks):
            start_time = i * chunk_duration_ms
            end_time = min((i + 1) * chunk_duration_ms, total_duration_ms)
            
            chunk = audio[start_time:end_time]
            chunks.append(chunk)
            
            # Save chunk to temporary file
            chunk_filename = f"{file_path}_chunk_{i+1}.mp3"
            chunk.export(chunk_filename, format="mp3")
            chunk_files.append(chunk_filename)
        
        return chunk_files, num_chunks
    except Exception as e:
        st.error(f"Error chunking audio file: {str(e)}")
        return [], 0

def cleanup_chunk_files(chunk_files):
    """Clean up temporary chunk files"""
    for chunk_file in chunk_files:
        try:
            if os.path.exists(chunk_file):
                os.unlink(chunk_file)
        except Exception:
            pass

def process_audio_with_genai(uploaded_file):
    """Process audio using Google GenAI client for better large file handling"""
    try:
        # Create a temporary file for the upload
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(uploaded_file.getbuffer())
            temp_file_path = temp_file.name
        
        # Check if file needs chunking (>25 minutes)
        duration_minutes = get_audio_duration(temp_file_path)
        
        if duration_minutes > 25:
            st.warning(f"⚠️ Large file detected ({duration_minutes:.1f} minutes). Processing in chunks to prevent truncation...")
            
            # Chunk the audio file
            chunk_files, num_chunks = chunk_audio_file(temp_file_path, chunk_duration_minutes=20)
            
            if not chunk_files:
                raise Exception("Failed to chunk audio file")
            
            st.info(f"📋 File split into {num_chunks} chunks for processing")
            
            # Initialize the GenAI client
            client = genai.Client()
            
            all_transcriptions = []
            
            # Process each chunk
            progress_bar = st.progress(0)
            for i, chunk_file in enumerate(chunk_files):
                chunk_number = i + 1
                progress_bar.progress(chunk_number / num_chunks)
                st.info(f"🔄 Processing chunk {chunk_number}/{num_chunks}...")
                
                # Upload chunk to Google's servers
                chunk_file_ref = client.files.upload(file=chunk_file)
                
                # Generate transcription for this chunk
                response = client.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=["Transcribe this audio file exactly as spoken.", chunk_file_ref]
                )
                
                chunk_transcription = response.text
                all_transcriptions.append(f"[Chunk {chunk_number}/{num_chunks}]\n{chunk_transcription}")
            
            # Clean up chunk files
            cleanup_chunk_files(chunk_files)
            
            # Combine all transcriptions
            combined_transcription = "\n\n".join(all_transcriptions)
            
            # Create a mock file reference for the combined result
            class MockFileRef:
                def __init__(self, transcription):
                    self.transcription = transcription
            
            mock_file_ref = MockFileRef(combined_transcription)
            
            # Clean up original temp file
            os.unlink(temp_file_path)
            
            return mock_file_ref, client, True  # True indicates chunked processing
            
        else:
            # Process normally for smaller files
            # Initialize the GenAI client
            client = genai.Client()
            
            # Upload file to Google's servers
            st.info("Uploading file to Google's servers for processing...")
            myfile = client.files.upload(file=temp_file_path)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return myfile, client, False  # False indicates normal processing
        
    except Exception as e:
        # Clean up temp file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        if 'chunk_files' in locals():
            cleanup_chunk_files(chunk_files)
        raise e

def generate_transcription(client, file_ref, is_chunked=False):
    """Generate transcription using the uploaded file reference"""
    if is_chunked:
        # Return the pre-processed transcription for chunked files
        return file_ref.transcription
    else:
        # Generate transcription normally for single files
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=["Transcribe this audio file exactly as spoken.", file_ref]
        )
        return response.text

def generate_conversation(client, transcription_text):
    """Generate formatted conversation from transcription"""
    # For very long transcriptions, we need to chunk this too
    if len(transcription_text) > 30000:  # Roughly estimate to stay under token limits
        st.info("📝 Large transcription detected. Processing conversation in segments...")
        
        # Split into segments
        words = transcription_text.split()
        chunk_size = 5000  # words per chunk
        chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        
        formatted_conversations = []
        
        for i, chunk in enumerate(chunks):
            st.info(f"🔄 Formatting conversation segment {i+1}/{len(chunks)}...")
            
            prompt = f"""Format this transcript segment as a clean conversation:
            {chunk}
            
            Format rules:
            1. Format the transcript as a clean conversation
            2. Use **Speaker:** format for names
            3. Add line breaks between speakers
            4. Keep medical terms exact
            5. Output only the formatted conversation
            6. If this is a segment from a longer conversation, continue the speaker identification from context
            """
            
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[prompt]
            )
            formatted_conversations.append(f"[Segment {i+1}]\n{response.text}")
        
        return "\n\n".join(formatted_conversations)
    else:
        # Process normally for shorter transcriptions
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
    # For very long transcriptions, we need to chunk this too
    if len(transcription_text) > 30000:  # Roughly estimate to stay under token limits
        st.info("📋 Large transcription detected. Processing summary in segments...")
        
        # Split into segments
        words = transcription_text.split()
        chunk_size = 5000  # words per chunk
        chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        
        segment_summaries = []
        
        for i, chunk in enumerate(chunks):
            st.info(f"🔄 Analyzing segment {i+1}/{len(chunks)}...")
            
            prompt = f"""Analyze this medical conversation segment and extract key information:
            {chunk}
            
            Extract and format the following information if present:
            - Patient information and demographics
            - Chief complaints and symptoms
            - Medical history mentioned
            - Medications discussed
            - Treatment plans or recommendations
            - Key medical findings
            
            Format as structured notes. If this is a segment, focus on the content present.
            """
            
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[prompt]
            )
            segment_summaries.append(f"**Segment {i+1} Analysis:**\n{response.text}")
        
        # Now generate final comprehensive summary
        combined_analysis = "\n\n".join(segment_summaries)
        
        final_prompt = f"""Create a comprehensive medical summary report from these segment analyses:
        
        {combined_analysis}
        
        Format the final report with these sections using markdown:
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

        Consolidate information from all segments into a coherent, comprehensive report.
        Use bullet points for easy reading and maintain medical terminology exactly as mentioned.
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[final_prompt]
        )
        return response.text
    else:
        # Process normally for shorter transcriptions
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
        
        # Estimate duration (rough calculation: ~1MB per minute for typical MP3)
        estimated_duration = file_size_mb * 1.0  # rough estimate
        
        if estimated_duration > 25:
            st.warning("⚠️ Large file detected. Will use chunked processing to prevent transcription cutoff.")
            st.info("📋 Files over 25 minutes are automatically split into 20-minute chunks for complete transcription.")
        
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
        file_ref, client, is_chunked = process_audio_with_genai(uploaded_file)
        
        if is_chunked:
            st.success("✅ Audio chunking completed successfully!")
        
        # Transcription
        with tab1:
            st.markdown("### Transcription")
            with st.spinner("Generating transcription..."):
                transcription_text = generate_transcription(client, file_ref, is_chunked)
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
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        processing_method = "Chunked" if is_chunked else "Direct"
        file_info = f"{uploaded_file.name} ({file_size_mb:.1f} MB) - {processing_method} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
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