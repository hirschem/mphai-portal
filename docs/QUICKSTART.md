# Quick Start Guide

## Backend Setup (COMPLETE THIS FIRST)

1. **Add your OpenAI API key to `.env` file:**
   - Open the `.env` file in the root directory
   - Replace `your_openai_api_key_here` with your actual OpenAI API key
   - Get key from: https://platform.openai.com/api-keys

2. **Start the backend server:**
   ```bash
   cd apps/api
   .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Frontend Setup

1. **Install dependencies:**
   ```bash
   cd apps/web
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

3. **Open browser:**
   - Visit: http://localhost:3000

## Testing

Upload the handwritten proposal images to test transcription and professional rewriting.

## For Production Deployment

Once tested locally, we'll prepare for deployment to your domain:
- Backend: Railway, Render, or AWS
- Frontend: Vercel, Netlify, or your hosting provider
- Database: Optional for storing proposals long-term
