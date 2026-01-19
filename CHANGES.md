# MPH Handwriting - Dual Mode System

## What Was Added

### Backend Changes

1. **Book OCR Service** (`book_ocr_service.py`)
   - Exact word-for-word transcription (no editing)
   - Multi-page processing with `[Page X]` markers
   - Strict GPT-4o prompt: "Transcribe EXACTLY as written, word-for-word"

2. **Book Export Service** (`book_export_service.py`)
   - Exports to editable Word documents (.docx)
   - Times New Roman 12pt font, 1-inch margins
   - Chapter title as Heading 1
   - Page breaks preserved from transcription

3. **Book API Endpoints** (`apps/api/app/api/books.py`)
   - `POST /api/book/upload` - Upload multiple images with chapter name
   - `GET /api/book/list` - List all chapters (admin only)
   - `GET /api/book/download/{chapter_id}` - Download Word document
   - `DELETE /api/book/{chapter_id}` - Delete chapter (admin only)

4. **File Storage** (`file_manager.py`)
   - `data/books/{chapter_id}/` directory structure
   - Saves pages as `page_001.jpg`, `page_002.jpg`, etc.
   - Stores metadata in `chapter.json`

5. **Invoice Pagination Fix** (`export_service.py`)
   - First page uses MPH template overlay
   - Additional pages are plain white (no template)
   - Automatic page breaks when content exceeds page limits

### Frontend Changes

1. **Mode Selector** (`ModeSelector.tsx`)
   - Displayed after login
   - Two large cards: Invoice Mode and Book Mode
   - Clear descriptions of each mode's purpose

2. **Invoice Mode Page** (`/invoice`)
   - Moved original upload form to `/invoice` route
   - Professional formatting and PDF generation
   - Link back to mode selector

3. **Book Mode Page** (`/book`)
   - Upload multiple images at once
   - Chapter name input field
   - Progress indicator during transcription
   - Display transcribed text
   - Download as Word document button

4. **Book History Page** (`/book/history`)
   - Grid of chapter cards (admin only)
   - Shows chapter name, page count, creation date
   - Download and delete buttons for each chapter

5. **Invoice History Page** (`/invoice/history`)
   - Moved from `/history` to `/invoice/history`
   - Updated navigation links

6. **Authentication Enhancement**
   - Added `getAuthHeader()` helper to AuthContext
   - Returns `Authorization: Bearer {password}` header

## Routes Summary

```
/ - Login or Mode Selector
/invoice - Invoice upload and generation
/invoice/history - Invoice history (admin only)
/book - Book chapter upload and transcription
/book/history - Chapter history (admin only)
```

## How to Use

### Invoice Mode
1. Login with demo2024 or admin password
2. Select "Invoice Mode"
3. Upload handwriting image
4. System rewrites professionally and generates PDF
5. Download PDF with MPH branding

### Book Mode
1. Login with demo2024 or admin password
2. Select "Book Mode"
3. Enter chapter name
4. Upload one or multiple page images
5. System transcribes exactly as written
6. Download editable Word document

## Technical Notes

- Book mode uses **exact transcription** (no AI rewriting)
- Invoice mode uses **professional rewriting** for proposals
- Multi-page uploads are processed sequentially
- Both modes support multi-page content
- Admin users can access history for both modes
- Demo users can use features but cannot see history

## Deployment

Changes are automatically deployed to:
- Backend: Railway (mph-handwriting-production.up.railway.app)
- Frontend: Vercel (mphai.app)

Railway will install python-docx dependency automatically from requirements.txt.
