import streamlit as st
from agentWorkflow import AudioTranscriptionWorkflow
from storage_helper import upload_file, verify_gcs_setup, get_signed_url
import time

def main():
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
    if 'gcs_path' not in st.session_state:
        st.session_state.gcs_path = None
    
    st.title("Report Generator Agent")
    
    with st.sidebar:
        st.header("Upload Recording")
        uploaded_file = st.file_uploader("Choose an MP3 file", type=['mp3'])
        
        if uploaded_file:
            # Immediately upload to GCS when file is selected
            try:
                with st.spinner("Uploading to cloud storage..."):
                    gcs_path = upload_file(uploaded_file, uploaded_file.name)
                    if gcs_path:
                        st.session_state.gcs_path = gcs_path
                        
                        # Get signed URL for audio player
                        signed_url = get_signed_url(gcs_path)
                        
                        st.write("File details:")
                        st.write(f"- Filename: {uploaded_file.name}")
                        
                        # Display audio player using signed URL
                        st.markdown("### Preview Audio")
                        st.audio(signed_url)
                        
                        process_button = st.button("Process Recording", type="primary", key="process_btn")
                        st.markdown("---")
                        progress_placeholder = st.empty()
                    else:
                        st.error("Failed to upload file to cloud storage")
            except Exception as e:
                st.error(f"Error during upload: {str(e)}")
    
    tabs = st.tabs(["Transcription", "Conversation"])
    
    if st.session_state.gcs_path and process_button:
        try:
            timestamp = int(time.time())
            workflow = AudioTranscriptionWorkflow()
            
            with progress_placeholder.container():
                st.info("Starting transcription process...")
                
                for response in workflow.run(
                    message=uploaded_file.name,
                    gcs_path=st.session_state.gcs_path  # Pass GCS path instead of audio content
                ):
                    if "Transcription completed" in response.content:
                        # Handle transcription
                        transcription = response.content.split("\n\n", 1)[1]
                        st.session_state.transcription = transcription
                        
                        with tabs[0]:
                            st.markdown(f"### Transcription\n\n{transcription}")
                            st.download_button(
                                "Download Transcription",
                                transcription,
                                file_name="transcription.txt",
                                mime="text/plain",
                                key=f"download_trans_{timestamp}"
                            )
                    else:
                        # Handle conversation
                        st.session_state.conversation_parts.append(response.content)
                        conversation_text = "\n\n".join(st.session_state.conversation_parts)
                        
                        with tabs[1]:
                            st.markdown(f"### Conversation\n\n{conversation_text}")
                            if conversation_text:
                                st.download_button(
                                    "Download Conversation",
                                    conversation_text,
                                    file_name="conversation.md",
                                    mime="text/markdown",
                                    key=f"download_conv_{timestamp}"
                                )
                    
                    progress_placeholder.info(f"Processing: {response.content[:50]}...")
                
                progress_placeholder.success("Processing completed!")
        
        except Exception as e:
            progress_placeholder.error(f"Error during processing: {str(e)}")
    
    # Display existing results if available
    if not st.session_state.processing:
        with tabs[0]:
            if st.session_state.transcription:
                st.markdown(f"### Transcription\n\n{st.session_state.transcription}")
                st.download_button(
                    "Download Transcription",
                    st.session_state.transcription,
                    file_name="transcription.txt",
                    mime="text/plain",
                    key="download_trans_existing"
                )
            else:
                st.info("Upload and process an audio file to see the transcription.")
        
        with tabs[1]:
            if st.session_state.conversation_parts:
                conversation_text = "\n\n".join(st.session_state.conversation_parts)
                st.markdown(f"### Conversation\n\n{conversation_text}")
                st.download_button(
                    "Download Conversation",
                    conversation_text,
                    file_name="conversation.md",
                    mime="text/markdown",
                    key="download_conv_existing"
                )
            else:
                st.info("Upload and process an audio file to see the conversation.")

if __name__ == "__main__":
    main() 