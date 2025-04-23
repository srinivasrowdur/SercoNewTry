import streamlit as st
from agentWorkflow import AudioTranscriptionWorkflow, ContentType
from storage_helper import upload_file, get_public_url
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
    if 'blob_name' not in st.session_state:
        st.session_state.blob_name = None
    
    st.title("Report Generator Agent")
    
    with st.sidebar:
        st.header("Upload Recording")
        uploaded_file = st.file_uploader("Choose an MP3 file", type=['mp3'])
        
        if uploaded_file:
            try:
                # Show file details first
                st.write("File details:")
                st.write(f"- Filename: {uploaded_file.name}")
                st.write(f"- File size: {uploaded_file.size/1024:.2f} KB")
                
                # Show audio preview using the uploaded file directly
                st.markdown("### Preview Audio")
                st.audio(uploaded_file)
                
                # Process button
                process_button = st.button("Process Recording", type="primary", key="process_btn")
                progress_placeholder = st.empty()
                
                if process_button:
                    with st.spinner("Uploading to cloud storage..."):
                        blob_name = upload_file(uploaded_file, uploaded_file.name)
                        if blob_name:
                            st.session_state.blob_name = blob_name
                            st.success("File uploaded successfully!")
                            
                            # Get public URL for processing
                            public_url = get_public_url(blob_name)
                            st.session_state.public_url = public_url
                        else:
                            st.error("Failed to upload file to cloud storage")
                
            except Exception as e:
                st.error(f"Error handling file: {str(e)}")
    
    tabs = st.tabs(["Transcription", "Conversation"])
    
    if st.session_state.get('public_url') and process_button:
        try:
            timestamp = int(time.time())
            workflow = AudioTranscriptionWorkflow()
            
            with progress_placeholder.container():
                st.info("Starting transcription process...")
                
                for response in workflow.run(
                    message=uploaded_file.name,
                    audio_url=st.session_state.public_url
                ):
                    if response.content_type == ContentType.ERROR:
                        progress_placeholder.error(response.content)
                        break
                        
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
                
                if not st.session_state.get('transcription'):
                    progress_placeholder.error("Failed to generate transcription")
                else:
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