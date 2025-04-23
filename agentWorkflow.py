from typing import Iterator
from agno.agent import Agent, RunResponse
from agno.models.google import Gemini
from agno.media import Audio
from agno.utils.log import logger
from agno.utils.pprint import pprint_run_response
from agno.workflow import Workflow
from dotenv import load_dotenv
import io
import requests
from enum import Enum
from dataclasses import dataclass

# Load environment variables
load_dotenv()

class ContentType(Enum):
    TEXT = "text"
    ERROR = "error"

@dataclass
class WorkflowResponse:
    content: str
    content_type: ContentType

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

    def __init__(self):
        super().__init__()
        self.agent = Agent(
            model=Gemini(id="gemini-2.0-flash-exp"),
            markdown=True,
        )

    def run(self, message: str, audio_url: str):
        """
        Run the transcription workflow using a public URL
        
        Args:
            message: The name or context of the audio file
            audio_url: Public URL to the audio file
        """
        try:
            # Download audio content from URL
            response = requests.get(audio_url)
            if response.status_code != 200:
                yield WorkflowResponse(
                    content=f"Error downloading audio: HTTP {response.status_code}",
                    content_type=ContentType.ERROR
                )
                return
                
            audio_content = response.content

            # First pass: Get transcription
            transcription_response = self.agent.get_response(
                "Please transcribe this audio file accurately, maintaining all speaker information.",
                audio=[Audio(content=audio_content)]
            )
            yield WorkflowResponse(
                content=f"Transcription completed\n\n{transcription_response}",
                content_type=ContentType.TEXT
            )

            # Second pass: Generate conversation
            conversation_prompt = """
            Based on the transcription above, please:
            1. Clearly identify all speakers
            2. Format the conversation in a clean, readable way
            3. Maintain the exact content and context
            4. Keep medical terminology precise
            5. Preserve any important pauses or non-verbal elements
            
            Please format it as a conversation.
            """
            
            conversation_response = self.agent.get_response(conversation_prompt)
            yield WorkflowResponse(
                content=conversation_response,
                content_type=ContentType.TEXT
            )

        except Exception as e:
            yield WorkflowResponse(
                content=f"Error during processing: {str(e)}",
                content_type=ContentType.ERROR
            )

def main():
    # Initialize workflow
    workflow = AudioTranscriptionWorkflow()
    
    # Audio file path
    audio_path = "BackPain.mp3"
    
    print(f"Processing audio file: {audio_path}")
    print("=" * 50)
    
    # Run workflow
    response = workflow.run(message=audio_path, audio_url="https://example.com/signed-url")
    
    # Print responses with formatting
    print("\nWorkflow Output:")
    print("=" * 50)
    pprint_run_response(response, markdown=True, show_time=True)
    
    # Run again to demonstrate caching
    print("\nRunning again (should be cached):")
    print("=" * 50)
    response = workflow.run(message=audio_path, audio_url="https://example.com/signed-url")
    pprint_run_response(response, markdown=True, show_time=True)

if __name__ == "__main__":
    main()
