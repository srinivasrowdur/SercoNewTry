# Medical Audio Transcription & Report Generator

A Streamlit-based application that converts medical audio recordings into structured transcriptions, formatted conversations, and comprehensive medical summary reports using Google's Gemini AI.

## 🎯 Overview

This application helps healthcare professionals and medical transcriptionists convert audio recordings of medical consultations into three formatted outputs:

1. **Raw Transcription** - Exact text transcription of the audio
2. **Formatted Conversation** - Clean, structured dialogue between speakers
3. **Medical Summary Report** - Comprehensive medical report with structured sections

## ✨ Features

- **Large File Support** - Optimized for handling large audio files (>100MB) using Google's file upload infrastructure
- **Real-time Processing** - Live progress updates during transcription and analysis
- **Multiple Output Formats** - Generate transcription (.txt), conversation (.md), and summary report (.md)
- **Session Persistence** - Results are cached during your session for easy access
- **Download Functionality** - Download any result with timestamped filenames
- **Audio Preview** - Built-in audio player for file verification before processing
- **File Size Monitoring** - Displays file size and warns for large files

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google API key for Gemini AI
- Audio files in MP3 format

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/srinivasrowdur/SercoNewTry.git
   cd SercoNewTry
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google AI API Key**
   - Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Set it as an environment variable:
     ```bash
     export GOOGLE_API_KEY="your-api-key-here"
     ```
   - Or create a `.env` file:
     ```
     GOOGLE_API_KEY=your-api-key-here
     ```

4. **Run the application**
   ```bash
   streamlit run streamlit_app.py
   ```

5. **Open your browser**
   - Navigate to `http://localhost:8501`

## 📋 How to Use

### Step 1: Upload Audio File
- Click "Choose an MP3 file" in the sidebar
- Select your medical audio recording
- Preview the audio using the built-in player
- Check the file size indicator

### Step 2: Process Recording
- Click the "Process Recording" button
- Wait for the file to upload to Google's servers
- Processing will happen across all three tabs automatically

### Step 3: Review Results
Navigate through the three tabs to see results:

#### 📄 Transcription Tab
- Raw text transcription of the audio
- Exact words as spoken
- Download as `.txt` file

#### 💬 Conversation Tab  
- Formatted dialogue with speaker identification
- Clean formatting with **Speaker:** labels
- Line breaks between speakers
- Download as `.md` file

#### 📋 Summary Report Tab
- Comprehensive medical report with structured sections:
  - **Patient Information** - Demographics and basic info
  - **Chief Complaint** - Main reason for visit
  - **History of Present Illness** - Symptom progression
  - **Past Medical History** - Previous conditions
  - **Current Medications** - Listed medications
  - **Treatment Plan** - Prescribed treatments
  - **Assessment** - Key findings and concerns
- Download as `.md` file

### Step 4: Download Results
- Use download buttons in each tab
- Files are automatically named with timestamps
- Results persist during your session

## 🔧 Technical Details

### Architecture
- **Frontend**: Streamlit web interface
- **AI Engine**: Google Gemini 2.0 Flash Experimental model
- **File Handling**: Google GenAI Client for optimized large file processing
- **Storage**: Temporary file handling with automatic cleanup

### Key Components

#### File Processing Pipeline
```
Audio Upload → Temporary File → Google's Servers → AI Processing → Results
```

#### AI Processing Chain
1. **Audio → Text**: Google Gemini transcribes audio to text
2. **Text → Conversation**: AI formats raw text into structured dialogue
3. **Text → Medical Report**: AI generates comprehensive medical summary

### Performance Optimizations
- **Large File Handling**: Files uploaded to Google's infrastructure for processing
- **Memory Efficiency**: No local storage of large files
- **Session Caching**: Results stored in session state
- **Automatic Cleanup**: Temporary files automatically removed

## 📁 File Structure

```
SercoNewTry/
├── streamlit_app.py          # Main application file
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── .env                     # Environment variables (optional)
├── .gitignore              # Git ignore rules
└── storage_helper.py       # GCS helper functions (unused in current version)
```

## 🛠 Dependencies

```
streamlit                    # Web framework
google-genai                # Google AI client
python-dotenv               # Environment variable management
requests                    # HTTP requests
pathlib                    # File path handling
pydub                       # Audio processing utilities
```

## ⚙️ Configuration

### Environment Variables
- `GOOGLE_API_KEY` - Your Google AI API key (required)

### File Size Limits
- **Recommended**: Files under 100MB for optimal performance
- **Supported**: Large files (>100MB) with optimized processing
- **Format**: MP3 audio files only

## 🔒 Privacy & Security

- **No Permanent Storage**: Audio files are processed and immediately deleted
- **Temporary Processing**: Files uploaded to Google's servers only during processing
- **Session-Based**: Results stored only in your browser session
- **No Data Retention**: No audio or text data is permanently stored by the application

## 🐛 Troubleshooting

### Common Issues

1. **"Authentication Error"**
   - Verify your Google API key is set correctly
   - Check the API key has access to Gemini models

2. **"File Upload Failed"**
   - Ensure file is in MP3 format
   - Check internet connection
   - Try with a smaller file first

3. **"Processing Timeout"**
   - Large files may take longer to process
   - Check your internet connection stability
   - Try refreshing and uploading again

4. **"Import Error"**
   - Run `pip install -r requirements.txt`
   - Ensure you're using Python 3.8+

### Performance Tips
- Use MP3 files for best compatibility
- For very large files (>500MB), consider splitting them
- Ensure stable internet connection for large file uploads

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Create an issue in the GitHub repository
3. Provide details about your environment and the specific error

## 🔄 Version History

- **v2.0.0** - Google GenAI integration with large file support
- **v1.0.0** - Initial release with agno framework

---

**Made with ❤️ for healthcare professionals** 