from typing import Iterator
from agno.agent import Agent, RunResponse
from agno.media import Audio
from agno.models.google import Gemini
from agno.workflow import Workflow
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioTranscriptionWorkflow(Workflow):
    def __init__(self, session_id="audio-transcription"):
        super().__init__(session_id=session_id)
        
        # Configure transcription agent
        self.transcription_agent = Agent(
            model=Gemini(id="gemini-2.0-flash-exp"),
            name="Transcription Agent",
            description="You are an expert transcriptionist who converts audio to accurate text.",
            markdown=False,
            instructions=[
                "Transcribe the audio exactly as spoken",
                "Include speaker names",
                "Output only the transcription"
            ],
            create_default_system_message=True
        )
        
        # Configure conversation formatting agent
        self.conversation_agent = Agent(
            model=Gemini(id="gemini-2.0-flash-exp"),
            name="Conversation Formatter",
            description="You are an expert at formatting transcripts into readable conversations.",
            markdown=True,
            instructions=[
                "Format the transcript as a clean conversation",
                "Use **Speaker:** format for names",
                "Add line breaks between speakers",
                "Keep medical terms exact",
                "Output only the formatted conversation"
            ],
            create_default_system_message=True
        )
        
        logger.info("Agents initialized successfully")

    def run(self, audio_path: str) -> Iterator[RunResponse]:
        try:
            # Check cache first
            cache_key = f"audio_{audio_path}"
            if cache_key in self.session_state:
                logger.info(f"Cache hit for {audio_path}")
                yield RunResponse(
                    run_id=self.run_id,
                    content=self.session_state[cache_key]["transcription"]
                )
                yield RunResponse(
                    run_id=self.run_id,
                    content=self.session_state[cache_key]["conversation"]
                )
                return

            logger.info(f"Processing audio file: {audio_path}")

            # Get transcription
            transcription = self.transcription_agent.run(
                "Transcribe this audio file.",
                audio=[Audio(filepath=audio_path)]
            )
            transcription_text = str(transcription)
            yield RunResponse(run_id=self.run_id, content=transcription_text)

            # Format as conversation
            self.conversation_agent.print_response(
                f"Format this transcript as a conversation:\n{transcription_text}",
                stream=True
            )
            conversation_text = str(self.conversation_agent.run_response)
            yield RunResponse(run_id=self.run_id, content=conversation_text)

            # Cache the results
            self.session_state[cache_key] = {
                "transcription": transcription_text,
                "conversation": conversation_text
            }

        except Exception as e:
            logger.error(f"Error during processing: {str(e)}")
            yield RunResponse(
                run_id=self.run_id,
                content=f"ERROR: {str(e)}"
            )
