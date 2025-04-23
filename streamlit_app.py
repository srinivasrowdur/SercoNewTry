import streamlit as st
from agno.agent import Agent
from agno.media import Audio
from agno.models.google import Gemini
from pathlib import Path
import os

def save_uploaded_file(uploaded_file, save_dir="uploads"):
    """Save uploaded file to local directory and return the file path"""
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(save_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

st.set_page_config(page_title="Report Generator Agent", layout="wide")
st.title("Report Generator Agent")

# Initialize agent once
if 'agent' not in st.session_state:
    st.session_state.agent = Agent(
        model=Gemini(id="gemini-2.0-flash-exp"),
        markdown=True
    )

# File uploader in sidebar
with st.sidebar:
    st.header("Upload Recording")
    uploaded_file = st.file_uploader("Choose an MP3 file", type=['mp3'])
    if uploaded_file:
        st.audio(uploaded_file)
        process_button = st.button("Process Recording", type="primary")

# Main content area with tabs
tab1, tab2, tab3 = st.tabs(["Transcription", "Conversation", "Summary Report"])

if uploaded_file and process_button:
    try:
        # Save and process file
        file_path = save_uploaded_file(uploaded_file)
        
        # Transcription
        with tab1:
            st.markdown("### Transcription")
            with st.spinner("Generating transcription..."):
                transcription_response = st.session_state.agent.run(
                    "Transcribe this audio file exactly as spoken.",
                    audio=[Audio(filepath=file_path)]
                )
                st.markdown(transcription_response.content)
        
        # Conversation formatting
        with tab2:
            st.markdown("### Conversation")
            with st.spinner("Formatting conversation..."):
                conversation_response = st.session_state.agent.run(
                    f"""Format this transcript as a clean conversation:
                    {str(transcription_response)}
                    
                    Format rules:
                    1. Format the transcript as a clean conversation
                    2. Use **Speaker:** format for names
                    3. Add line breaks between speakers
                    4. Keep medical terms exact
                    5. Output only the formatted conversation
                    """
                )
                st.markdown(conversation_response.content)

        # Summary Report
        with tab3:
            st.markdown("### Summary Report")
            with st.spinner("Generating summary report..."):
                summary_response = st.session_state.agent.run(
                    f"""Create a detailed medical summary report from this conversation:
                    {str(transcription_response)}
                    
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
                )
                st.markdown(summary_response.content)
        
        # Cleanup
        os.remove(file_path)
        st.success("Processing completed!")
        
    except Exception as e:
        st.error(f"Error: {str(e)}") 