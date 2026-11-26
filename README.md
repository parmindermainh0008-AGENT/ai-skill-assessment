# AI Skill Assessment

A Streamlit app that generates and evaluates interview-preparation quizzes using an LLM.

## Features
- Google sign-in
- AI-generated quiz questions on a topic of your choice
- AI evaluation of your answers with feedback
- Quiz history stored in a local SQLite database

## Project structure
| File | Purpose |
|------|---------|
| `app.py` | Streamlit user interface (main entry point) |
| `auth.py` | Login and authentication |
| `config.py` | Settings and environment variables |
| `db.py` | Database setup and queries |
| `llm_service.py` | Quiz generation and answer evaluation with the LLM |
| `requirements.txt` | Python dependencies |

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/parmindermainh0008-AGENT/ai-skill-assessment.git
   cd ai-skill-assessment
   ```
2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project folder (see `.env.example`) and add your API key.
4. Download your own Google OAuth client file from Google Cloud Console and save it as `google_client_secret.json` in the project folder.
5. Run the app:
   ```
   streamlit run app.py
   ```

The database file `quiz_app.db` is created automatically on the first run.

## Tech stack
Python, Streamlit, SQLite, LLM API

## Author
Parminder Singh, BCA (AI & DS), CT University, Ludhiana
