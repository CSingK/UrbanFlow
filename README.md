# UrbanFlow

AI-powered mobility orchestrator for the **Johor-Singapore Special Economic Zone (JS-SEZ)**. Synchronizing carpools, bus boarding, and smart parking with the RTS Link via a verifiable Carbon Ledger.

Built for the **MyAI Future Hackathon (Track 4: Green Horizon)** using **Antigravity**.

## Core Features
- **🛡️ Urban Watch (PBT-Vision)**: Autonomous AI enforcement for parking violations, lane hogging, and illegal driving actions powered by **Gemini 2.5 Flash**.
- **🚗 Carpool Agent**: AI-driven matching to reduce single-occupancy vehicles on the Causeway.
- **🚌 Bus Intelligence**: Real-time transit optimization for first-mile/last-mile connectivity.
- **🌿 National Carbon Ledger**: A verifiable system to reward sustainable mobility choices.

## Project Structure
This application follows a standard FastAPI structure:
- `app/api/`: API router endpoints
- `app/models/`: SQLAlchemy database models
- `app/schemas/`: Pydantic models for data validation
- `app/services/`: Core business logic and external service integrations
- `app/database.py`: Async database setup and session management
- `app/main.py`: FastAPI application entry point

## Database Schema
The database uses PostgreSQL via asynchronous SQLAlchemy (`asyncpg`). All primary keys use UUIDs, and timestamps are configured for UTC+8.

The models included are:
- `users`
- `rts_schedules`
- `trips`
- `bus_stations`
- `carbon_ledger`

## Setup & Run Locally

1. Create a virtual environment and install the requirements:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

2. Run the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload
   ```

3. Run the Streamlit Dashboard:
   ```bash
   streamlit run dashboard.py
   ```
