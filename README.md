# Talk-to-Text

**Talk-to-Text** is a FastAPI application that converts spoken audio into text using **Google Cloud Speech-to-Text**, then generates concise summaries. It is designed with **multi‑speaker conversations in mind**, ideally suited for structured contexts such as **doctor–patient interactions** where accurate transcription and summarization are critical.

---

## Features
- **Google Cloud Speech-to-Text**: Accurate transcription of audio files and streams.
- **Multi‑Speaker Support**: Handles conversations between multiple speakers (e.g., doctor and patient).
- **Summarization**: Generates concise summaries of transcripts for quick review.
- **Streaming Support**: Real-time transcription via WebSocket endpoints.
- **REST API**: FastAPI routes for audio file upload and real-time transcription.
- **Healthcare Context Ready**: Tailored for medical consultations, but adaptable to other domains.

---

## Project Structure
```
├── app.py              # Main application entrypoint
├── requirements.txt    # Python dependencies
├── static/             # Static assets
├── utils/              # Helper functions
└── README.md           # Project documentation
```

---

## Installation

### Prerequisites
- Python 3.9+
- FastAPI
- Uvicorn
- Google Cloud SDK configured with Speech-to-Text enabled

### Setup
```bash
# Clone the repo
git clone https://github.com/mpiers110/talk-to-text.git
cd talk-to-text

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app:app --reload
```

---

## Documentation

### `GET /docs`
Interactive API documentation powered by **FastAPI + Swagger UI**.  
Use this endpoint to explore and test all available routes.

---

## Roadmap
- [ ] Improve speaker diarization for clearer multi‑speaker separation
- [ ] Frontend dashboard for managing transcripts and summaries
- [ ] HIPAA/GDPR compliance modules for healthcare deployments

---

## Contributing
Contributions are welcome! Please fork the repo and submit a pull request. For major changes, open an issue first to discuss what you’d like to change.

---

## License
MIT License – free to use, modify, and distribute.
