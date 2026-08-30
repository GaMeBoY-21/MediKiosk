# MediKiosk

An AI-assisted patient intake kiosk that conducts a guided interview, extracts structured clinical data, and hands off a physician-reviewable summary.

## Setup

1. Create a virtual environment and install backend dependencies:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in the values.
3. Run the backend:
   ```
   uvicorn app.main:app --reload
   ```
4. Install and run the frontend:
   ```
   cd frontend
   npm install
   npm run dev
   ```
