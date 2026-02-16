'use client';

import { useState, useRef } from 'react'
import Image from 'next/image';
import { apiFetchWithMeta } from '@/lib/apiClient'

interface UploadFormProps {
  onSuccess: (sessionId: string, proposalData: unknown) => void
}

export default function UploadForm({ onSuccess }: UploadFormProps) {
  const [files, setFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [previews, setPreviews] = useState<string[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)
  const cameraInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files
    if (selectedFiles && selectedFiles.length > 0) {
      const newFiles = Array.from(selectedFiles)
      // Add to existing files instead of replacing
      const allFiles = [...files, ...newFiles]
      setFiles(allFiles)
      setError(null)
      
      // Create previews for all files
      const previewPromises = allFiles.map(file => {
        return new Promise<string>((resolve) => {
          const reader = new FileReader()
          reader.onloadend = () => {
            resolve(reader.result as string)
          }
          reader.readAsDataURL(file)
        })
      })
      
      Promise.all(previewPromises).then(setPreviews)
      
      // Reset input so the same file can be selected again
      e.target.value = ''
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (files.length === 0) {
      setError('Please select at least one image or take a photo')
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Step 1: Upload and transcribe (use first file for now, can be enhanced for multi-page)
      const fd = new FormData();
      fd.append('file', files[0]);
      // TEMP upload debug logs
      console.log('UPLOAD DEBUG — fd type:', Object.prototype.toString.call(fd));
      console.log('UPLOAD DEBUG — instanceof FormData:', fd instanceof FormData);
      console.log('UPLOAD DEBUG — file constructor:', files?.[0]?.constructor?.name);
      type TranscribeResponse = { session_id: string; raw_text: string };
      const transcribeResp = await apiFetchWithMeta<TranscribeResponse>('/api/transcribe/upload', {
        method: 'POST',
        body: fd,
      });
      if (!transcribeResp.ok) throw transcribeResp.error || new Error('Failed to transcribe');
      if (!transcribeResp.data) throw new Error('Missing transcribe response');
      const tr = transcribeResp.data;

      // Step 2: Generate professional proposal
      type ProposalResponse = { session_id: string } & Record<string, unknown>;
      const proposalResp = await apiFetchWithMeta<ProposalResponse>('/api/proposals/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: tr.session_id,
          raw_text: tr.raw_text,
        }),
      });
      if (!proposalResp.ok) throw proposalResp.error || new Error('Failed to generate proposal');
      if (!proposalResp.data) throw new Error('Missing proposal response');
      const proposalResult = proposalResp.data;

      onSuccess(proposalResult.session_id, proposalResult);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'message' in err && typeof (err as { message?: unknown }).message === 'string') {
        setError((err as { message: string }).message || 'Failed to process image');
      } else {
        setError('Failed to process image');
      }
    } finally {
      setLoading(false)
    }
  }

  const handleCameraClick = () => {
    cameraInputRef.current?.click()
  }

  const handleFileClick = () => {
    fileInputRef.current?.click()
  }

  const clearImage = () => {
    setFiles([])
    setPreviews([])
    setError(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
    if (cameraInputRef.current) cameraInputRef.current.value = ''
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      {/* Hidden inputs - always rendered */}
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleFileChange}
        className="hidden"
        multiple
      />
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
        multiple
      />
      
      <form onSubmit={handleSubmit} className="space-y-4">
        {previews.length === 0 ? (
          <div className="space-y-4">
            <p className="text-center text-gray-600 mb-4 text-lg">
              Choose how to add your proposal:
            </p>
            
            {/* Camera Button */}
            <button
              type="button"
              onClick={handleCameraClick}
              className="w-full bg-blue-600 text-white py-6 px-6 rounded-xl
                hover:bg-blue-700 transition-colors font-semibold text-xl
                flex items-center justify-center gap-3 shadow-lg"
            >
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Take Photo
            </button>
            
            {/* File Upload Button */}
            <button
              type="button"
              onClick={handleFileClick}
              className="w-full bg-gray-100 text-gray-700 py-6 px-6 rounded-xl
                hover:bg-gray-200 transition-colors font-semibold text-xl
                flex items-center justify-center gap-3 shadow-lg"
            >
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Choose from Gallery
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-gray-600 mb-2 font-medium">
              {previews.length} image{previews.length !== 1 ? 's' : ''} selected
            </p>
            <div className="grid grid-cols-2 gap-4">
              {previews.map((preview, idx) => (
                <div key={idx} className="relative">
                  <Image
                    src={preview}
                    alt={`Preview ${idx + 1}`}
                    width={256}
                    height={256}
                    className="w-full h-auto rounded-lg border-2 border-gray-200"
                  />
                  <div className="absolute top-2 left-2 bg-blue-600 text-white px-2 py-1 rounded text-xs font-bold">
                    Page {idx + 1}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleFileClick}
                className="flex-1 bg-blue-100 text-blue-700 py-3 px-4 rounded-lg
                  hover:bg-blue-200 transition-colors font-medium flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M12 4v16m8-8H4" />
                </svg>
                Add More Photos
              </button>
              
              <button
                type="button"
                onClick={clearImage}
                className="bg-gray-100 text-gray-700 py-3 px-4 rounded-lg
                  hover:bg-gray-200 transition-colors font-medium"
              >
                Clear All
              </button>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-green-600 text-white py-4 px-4 rounded-xl
                hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed
                font-semibold transition-colors text-lg shadow-lg"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-6 w-6" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" 
                      stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" 
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Processing...
                </span>
              ) : (
                'Generate Professional Proposal'
              )}
            </button>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}
      </form>
    </div>
  )
}
