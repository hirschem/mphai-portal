'use client';

import { useRouter } from 'next/navigation';

export default function ModeSelector() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            MPH Handwriting
          </h1>
          <p className="text-lg text-gray-600">
            Choose your mode to get started
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Invoice Mode */}
          <button
            onClick={() => router.push('/invoice')}
            className="group relative bg-white p-8 rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 hover:scale-105 border-2 border-gray-100 hover:border-blue-500"
          >
            <div className="absolute top-4 right-4">
              <div className="w-3 h-3 bg-blue-500 rounded-full group-hover:animate-pulse"></div>
            </div>
            
            <div className="text-center">
              <div className="mb-4">
                <svg className="w-16 h-16 mx-auto text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              
              <h2 className="text-2xl font-bold text-gray-900 mb-3">
                Invoice Mode
              </h2>
              
              <p className="text-gray-600 mb-4">
                Transform handwritten proposals into professional invoices with MPH branding
              </p>
              
              <ul className="text-left space-y-2 text-sm text-gray-500">
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Professional formatting & rewriting</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>PDF generation with company template</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Automatic pricing calculations</span>
                </li>
              </ul>
            </div>
          </button>

          {/* Book Mode */}
          <button
            onClick={() => router.push('/book')}
            className="group relative bg-white p-8 rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 hover:scale-105 border-2 border-gray-100 hover:border-green-500"
          >
            <div className="absolute top-4 right-4">
              <div className="w-3 h-3 bg-green-500 rounded-full group-hover:animate-pulse"></div>
            </div>
            
            <div className="text-center">
              <div className="mb-4">
                <svg className="w-16 h-16 mx-auto text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              
              <h2 className="text-2xl font-bold text-gray-900 mb-3">
                Book Mode
              </h2>
              
              <p className="text-gray-600 mb-4">
                Exact word-for-word transcription of handwritten book chapters
              </p>
              
              <ul className="text-left space-y-2 text-sm text-gray-500">
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Word-for-word transcription (no editing)</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Export to editable Word documents</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Multi-page chapter support</span>
                </li>
              </ul>
            </div>
          </button>
        </div>

        <div className="mt-8 text-center">
          <button
            onClick={() => router.push('/invoice/history')}
            className="text-gray-500 hover:text-gray-700 text-sm underline"
          >
            View History
          </button>
        </div>
      </div>
    </div>
  );
}
