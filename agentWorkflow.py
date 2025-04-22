from typing import Iterator
from agno.agent import Agent, RunResponse
from agno.models.google import Gemini
from agno.media import Audio
from agno.utils.log import logger
from agno.utils.pprint import pprint_run_response
from agno.workflow import Workflow
from dotenv import load_dotenv
import io

# Load environment variables
load_dotenv()

class AudioTranscriptionWorkflow(Workflow):
    description: str = "A workflow that processes audio transcription and conversation generation"

    # First agent for audio transcription
    audio_agent = Agent(
        model=Gemini(id="gemini-2.0-flash-exp"),
        markdown=True
    )
    
    # Second agent for text processing
    text_agent = Agent(
        model=Gemini(id="gemini-2.0-flash-exp"),
        markdown=True
    )

    def run(self, message: str, audio_content: bytes = None) -> Iterator[RunResponse]:
        logger.info(f"Processing audio file")
        
        try:
            # Check if result is cached
            if self.session_state.get(message):
                logger.info(f"Cache hit for '{message}'")
                yield RunResponse(run_id=self.run_id, content=self.session_state[message])
                return

            # Step 1: Audio Transcription
            logger.info("Starting audio transcription...")
            
            # Create Audio object from bytes
            audio = Audio(content=audio_content, format='mp3')
            
            transcription_response = self.audio_agent.run(
                "Transcribe the contents of the audio file",
                audio=[audio]
            )
            
            yield RunResponse(
                run_id=self.run_id,
                content=f"Transcription completed:\n\n{transcription_response.content}"
            )

            # Step 2: Generate Conversation
            logger.info("Generating conversation from transcription...")
            conversation_prompt = (
                "Please create a detailed conversation of the transcription between "
                "the two people in the transcription, clearly identify the speakers. "
                f"Transcription: {transcription_response.content}"
            )

            # Process conversation and stream results
            yield from self.text_agent.run(
                conversation_prompt,
                stream=True
            )

            # Cache the final result
            self.session_state[message] = self.text_agent.run_response.content

        except Exception as e:
            error_msg = f"Error in workflow: {str(e)}"
            logger.error(error_msg)
            yield RunResponse(run_id=self.run_id, content=error_msg)

def main():
    # Initialize workflow
    workflow = AudioTranscriptionWorkflow()
    
    # Audio file path
    audio_path = "BackPain.mp3"
    
    print(f"Processing audio file: {audio_path}")
    print("=" * 50)
    
    # Run workflow
    response = workflow.run(message=audio_path)
    
    # Print responses with formatting
    print("\nWorkflow Output:")
    print("=" * 50)
    pprint_run_response(response, markdown=True, show_time=True)
    
    # Run again to demonstrate caching
    print("\nRunning again (should be cached):")
    print("=" * 50)
    response = workflow.run(message=audio_path)
    pprint_run_response(response, markdown=True, show_time=True)

if __name__ == "__main__":
    main()
