# Pre-Commit Preflight

Before every commit, run the preflight script to verify the project is ready to ship:

```powershell
scripts/preflight.ps1
```

Then review and check off each item in PRECOMMIT_CHECKLIST.md.
# MPH Handwriting Pipeline

Transform handwritten residential construction proposals into professional, customer-ready documents.

## Project Structure

- **apps/web** - Next.js frontend for uploading images and viewing proposals
- **apps/api** - FastAPI backend for OCR, transcription, and document generation
- **scripts** - Utilities for PDF splitting, dataset building, and accuracy evaluation
- **data** - Storage for uploads, sessions, and ground truth corrections

## Quick Start

### Backend Setup

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

Create `.env` file:
```
OPENAI_API_KEY=your_key_here
```

Run API:
```bash
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd apps/web
npm install
npm run dev
```

Visit: http://localhost:3000

## Usage

1. Take a photo of handwritten proposal
2. Upload via web interface
3. System transcribes and rewrites professionally
4. Export as PDF/Word document

## Features

- GPT-4 Vision OCR
- Professional rewriting for construction industry
- Structured data extraction
- Invoice generation (template integration pending)
- Ground truth tracking for accuracy evaluation
