import os
from agno.agent import Agent, RunResponse  # noqa
from agno.media import Audio
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
from dotenv import load_dotenv
import requests

# First install the required packages
# pip install python-dotenv agno requests

# Load environment variables from .env file
load_dotenv()

def main():
    try:

        # Read the local BackPain.mp3 file
        audio_path = "BackPain.mp3"
        
        print(f"Reading audio file from: {audio_path}")
        with open(audio_path, "rb") as audio_file:
            audio_data = audio_file.read()
        
        print("Creating agent...")
        # Provide the agent with the audio file and get result as text
        agent = Agent(
           model=Gemini(id="gemini-2.5-pro-preview-05-06"),
            markdown=True,
        )
        
        print("Processing audio...")
        # Process the audio and get response

        transcription = agent.run(
            "Transcribe the contents of the audio file", 
            audio=[Audio(filepath=audio_path)]
        )
        print(transcription)
        agent2 = Agent(
            model=Gemini(id="gemini-2.5-pro-preview-05-06"),
            markdown=True,
        )

        agent2.print_response(
            "Please create a detailed conversation of the transcription between the two people in the transcription, clearly identify the speakers " + transcription, 
            stream=True
        )

    except FileNotFoundError:
        print(f"Error: Could not find the audio file at {audio_path}")
        print("Make sure BackPain.mp3 is in the same directory as this script")
    except Exception as e:
        print(f"Error processing audio: {str(e)}")

if __name__ == "__main__":
    main()
