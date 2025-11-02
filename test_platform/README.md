# Test Assessment Platform (Streamlit)

Enterprise-grade Pre/Post Test Assessment Platform built with Streamlit, SQLAlchemy, PostgreSQL, and OpenAI.

## Features
- **Role-based auth**: Teacher and Student roles, bcrypt-hashed passwords
- **Test builder**: Create tests and add MCQ questions (4 options, correct index)
- **AI generation**: Generate validated questions via OpenAI GPT-3.5-turbo
- **Access keys**: Publish tests with shareable access keys
- **Test taking**: Students take tests, answers validated, automatic scoring
- **Analytics**: Score distribution, pre/post comparison, top performers, tables
- **Robust validation**: Pydantic schemas and custom validators
- **Logging**: Structured logging in production, human-readable in dev
- **DB pooling**: Environment-aware SQLAlchemy engine with pooling

## Tech Stack
- Frontend: Streamlit 1.40+
- Backend: Python 3.11, SQLAlchemy 2.0
- DB: PostgreSQL
- AI: OpenAI (gpt-3.5-turbo)
- PDF: ReportLab (placeholder in requirements for future reports)
- Validation: Pydantic v2
- Security: bcrypt
- Charts: Plotly + Pandas

## Project Structure
```
test_platform/
├── config/
│   ├── __init__.py
│   └── settings.py
├── database/
│   ├── __init__.py
│   ├── models.py
│   ├── schemas.py
│   └── crud.py
├── auth/
│   ├── __init__.py
│   └── authenticator.py
├── services/
│   ├── __init__.py
│   ├── test_service.py
│   ├── attempt_service.py
│   └── ai_service.py
├── components/
│   ├── __init__.py
│   ├── forms.py
│   └── charts.py
├── pages/
│   ├── 1_📊_Dashboard.py
│   ├── 2_✏️_Create_Test.py
│   ├── 3_🤖_AI_Generate.py
│   ├── 4_📝_Take_Test.py
│   └── 5_📈_Analytics.py
├── .streamlit/
│   └── config.toml
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Prerequisites
- Python 3.11
- PostgreSQL running locally or remote URL
- OpenAI API key (for AI generator)

## Setup
1. Clone repo and enter the folder
2. Create and activate a virtualenv
3. Copy `.env.example` to `.env` and update values
4. Install dependencies

```bash
pip install -r requirements.txt
```

Ensure the database from `DATABASE_URL` exists and is reachable by the app user.

## Running the App
```bash
streamlit run test_platform/app.py
```

Open your browser at the URL shown by Streamlit. Use the sidebar to navigate pages.

## Usage
- Register as Teacher or Student on the landing screen
- Teachers:
  - Create tests under "✏️ Create Test"
  - Optionally generate questions using "🤖 AI Question Generator"
  - Publish the test to generate an access key
- Students:
  - Use "📝 Take Test" to enter the access key and take the test
  - View analytics on "📈 Analytics"

## Environment Configuration
- Managed via Pydantic settings in `config/settings.py`
- Key variables: `ENVIRONMENT`, `DEBUG`, `DATABASE_URL`, `OPENAI_API_KEY`, `SECRET_KEY`

## Logging
- Development: human-readable logs to stdout
- Production: JSON logs to stdout

## Database & Migrations
- SQLAlchemy 2.0 models in `database/models.py`
- For production, use Alembic for migrations

## Security Notes
- Passwords hashed with bcrypt (12 rounds)
- Inputs validated and sanitized
- Never log sensitive data

## Testing
- Add unit tests for validators and services using `pytest`
- Mock OpenAI in tests

## Contributing
- Format with `black`
- Follow PEP8, docstrings, and type hints
- Open PRs with clear descriptions

## License
MIT
