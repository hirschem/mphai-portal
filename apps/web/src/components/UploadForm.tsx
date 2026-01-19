'use client'

import { useState, useRef } from 'react'
import { uploadAndTranscribe, generateProposal } from '@/lib/api'

interface UploadFormProps {
  onSuccess: (sessionId: string, proposalData: any) => void
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
      const filesArray = Array.from(selectedFiles)
      setFiles(filesArray)
      setError(null)
      
      // Create previews for all files
      const previewPromises = filesArray.map(file => {
        return new Promise<string>((resolve) => {
          const reader = new FileReader()
          reader.onloadend = () => {
            resolve(reader.result as string)
          }
          reader.readAsDataURL(file)
        })
      })
      
      Promise.all(previewPromises).then(setPreviews)
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
      const transcribeResult = await uploadAndTranscribe(files[0])
      
      // Step 2: Generate professional proposal
      const proposalResult = await generateProposal(
        transcribeResult.session_id,
        transcribeResult.raw_text
      )
      
      onSuccess(proposalResult.session_id, proposalResult)
    } catch (err: any) {
      setError(err.message || 'Failed to process image')
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

            {/* Hidden inputs */}
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
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-gray-600 mb-2">
              {previews.length} image{previews.length !== 1 ? 's' : ''} selected
            </p>
            <div className="grid grid-cols-2 gap-4">
              {previews.map((preview, idx) => (
                <div key={idx} className="relative">
                  <img
                    src={preview}
                    alt={`Preview ${idx + 1}`}
                    className="w-full h-auto rounded-lg border-2 border-gray-200"
                  />
                  <div className="absolute top-2 left-2 bg-blue-600 text-white px-2 py-1 rounded text-xs font-bold">
                    Page {idx + 1}
                  </div>
                </div>
              ))}
            </div>
            <div className="relative"
              <button
                type="button"
                onClick={clearImage}
                className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-2
                  hover:bg-red-600 transition-colors shadow-lg"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M6 18L18 6M6 6l12 12" />
                </svg>
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

            <button
              type="button"
              onClick={clearImage}
              className="w-full bg-gray-100 text-gray-700 py-3 px-4 rounded-lg
                hover:bg-gray-200 transition-colors font-medium"
            >
              Choose Different Photo
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
