
"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { apiFetchOptional, apiFetchWithMeta } from "@/lib/apiClient";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";

type BookUploadResponse = {
  transcribed_text: string;
  chapter_id: string;
};

export default function BookPage() {
  const [chapterName, setChapterName] = useState('')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [transcribedText, setTranscribedText] = useState('')
  const [chapterId, setChapterId] = useState('')
  const [error, setError] = useState('')
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const { isAdmin, logout } = useAuth()
  const hydratedRef = useRef(false)
  const dirtyRef = useRef(false)
  // Mark as dirty on any user interaction
  const markDirty = () => { dirtyRef.current = true }

  // Choose entity_id for admin persistence
  const entityId = chapterId || 'current'

  // Hydrate from admin persistence on mount (admin only, not dirty)
  useEffect(() => {
    if (!isAdmin) return;
    if (hydratedRef.current || dirtyRef.current) return;
    apiFetchOptional(`/api/admin-saves/book/${entityId}`)
      .then(({ ok, data }) => {
        if (ok && data && !dirtyRef.current) {
          const saved = (data ?? {}) as { chapterName?: string; selectedFiles?: unknown; transcribedText?: string; chapterId?: string };
          if (saved.chapterName) setChapterName(saved.chapterName)
          if (saved.selectedFiles) setSelectedFiles([]) // cannot hydrate File objects
          if (saved.transcribedText) setTranscribedText(saved.transcribedText)
          if (saved.chapterId) setChapterId(saved.chapterId)
          hydratedRef.current = true
        }
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin]);

  // Persist to admin-saves on save/upload (admin only)
  const persistAdminSave = useCallback(() => {
    if (!isAdmin) return;
    setSaveStatus('saving')
    apiFetchOptional(`/api/admin-saves/book/${entityId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chapterName,
        // selectedFiles cannot be persisted (File objects), skip
        transcribedText,
        chapterId,
      }),
    }).then(({ ok }) => {
      setSaveStatus(ok ? 'saved' : 'error')
      if (ok) setTimeout(() => setSaveStatus('idle'), 1200)
    }).catch(() => setSaveStatus('error'))
  }, [isAdmin, entityId, chapterName, transcribedText, chapterId])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const filesArray = Array.from(e.target.files)
      setSelectedFiles(filesArray)
      setError('')
      markDirty()
    }
  }

  const handleUpload = async () => {
    if (!chapterName.trim()) {
      setError('Please enter a chapter name')
      return
    }
    if (selectedFiles.length === 0) {
      setError('Please select at least one image')
      return
    }
    setIsLoading(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('chapter_name', chapterName)
      selectedFiles.forEach(file => {
        formData.append('files', file)
      })
      const { ok, data } = await apiFetchWithMeta<BookUploadResponse>('/api/book/upload', {
        method: 'POST',
        body: formData,
      });
      if (!ok || !data) {
        throw new Error('Upload failed');
      }
      setTranscribedText(data.transcribed_text);
      setChapterId(data.chapter_id);
      markDirty();
      persistAdminSave();
    } catch (err) {
      setError('Failed to transcribe chapter. Please try again.')
      console.error(err)
      setSaveStatus('error')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownload = async () => {
    markDirty()
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/book/download/${chapterId}`
      )
      
      if (!response.ok) throw new Error('Download failed')
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${chapterName}.docx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError('Failed to download document')
      console.error(err)
    }
  }

  const handleNewChapter = () => {
    setChapterName('')
    setSelectedFiles([])
    setTranscribedText('')
    setChapterId('')
    setError('')
    markDirty()
    persistAdminSave()
  }

  // Dev-only admin save key hint
  const devSaveKey = process.env.NODE_ENV !== 'production' && isAdmin
    ? `book/${chapterId || 'current'}`
    : null

  return (
    <main className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {devSaveKey && (
          <div style={{ fontSize: 12, color: '#888', marginBottom: 8, userSelect: 'all' }}>
            <span style={{ background: '#f3f3f3', padding: '2px 6px', borderRadius: 4 }}>
              [dev] admin save key: {devSaveKey}
            </span>
          </div>
        )}
        <header className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <Link 
                href="/"
                className="text-green-600 hover:text-green-700 text-sm mb-2 inline-block"
              >
                ← Back to Mode Selection
              </Link>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                Book Mode
              </h1>
              <p className="text-gray-600">
                Exact word-for-word transcription of handwritten chapters
              </p>
            </div>
            <div className="flex gap-3">
              {isAdmin && (
                <Link
                  href="/book/history"
                  className="bg-gray-700 text-white px-4 py-2 rounded-lg
                    hover:bg-gray-800 transition-colors flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  View Chapters
                </Link>
              )}
              <button
                onClick={logout}
                className="bg-red-600 text-white px-4 py-2 rounded-lg
                  hover:bg-red-700 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </header>

        {!transcribedText ? (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-6">Upload Chapter</h2>
            
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                {error}
              </div>
            )}

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Chapter Name
                </label>
                <input
                  type="text"
                  value={chapterName}
                  onChange={(e) => { setChapterName(e.target.value); markDirty(); }}
                  placeholder="e.g., Chapter 1: The Beginning"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg
                    focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  disabled={isLoading}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload Pages (Multiple Images)
                </label>
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handleFileSelect}
                  className="block w-full text-sm text-gray-500
                    file:mr-4 file:py-2 file:px-4
                    file:rounded-lg file:border-0
                    file:text-sm file:font-semibold
                    file:bg-green-50 file:text-green-700
                    hover:file:bg-green-100
                    cursor-pointer"
                  disabled={isLoading}
                />
                {selectedFiles.length > 0 && (
                  <p className="mt-2 text-sm text-gray-600">
                    {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''} selected
                  </p>
                )}
              </div>

              <button
                onClick={handleUpload}
                disabled={isLoading || !chapterName || selectedFiles.length === 0}
                className="w-full bg-green-600 text-white py-3 rounded-lg
                  hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed
                  transition-colors font-medium flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" 
                        stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" 
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Transcribing {selectedFiles.length} page{selectedFiles.length !== 1 ? 's' : ''}...
                  </>
                ) : (
                  'Transcribe Chapter'
                )}
              </button>
              {isAdmin && (
                <div className="mt-2 text-xs text-gray-500">
                  {saveStatus === 'saving' && 'Saving...'}
                  {saveStatus === 'saved' && 'Saved'}
                  {saveStatus === 'error' && 'Save failed'}
                </div>
              )}
            </div>

            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> This mode performs exact word-for-word transcription. 
                No editing or formatting changes will be made to the original text.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-lg p-8">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-2xl font-bold">{chapterName}</h2>
                  <p className="text-gray-600">Word-for-word transcription complete</p>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={handleDownload}
                    className="bg-green-600 text-white px-6 py-2 rounded-lg
                      hover:bg-green-700 transition-colors flex items-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                        d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Download Word Doc
                  </button>
                  <button
                    onClick={handleNewChapter}
                    className="bg-gray-600 text-white px-6 py-2 rounded-lg
                      hover:bg-gray-700 transition-colors"
                  >
                    New Chapter
                  </button>
                </div>
              </div>

              <div className="prose max-w-none">
                <div className="whitespace-pre-wrap font-mono text-sm bg-gray-50 p-6 rounded-lg border border-gray-200">
                  {transcribedText}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
