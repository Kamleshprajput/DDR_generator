'use client';

import { useState } from 'react';
import Uploader from '@/components/Uploader';
import ReportViewer from '@/components/ReportViewer';
import { DDRReport, ExtractedImage } from '@/lib/parseReport';

type LoadingStep = 'idle' | 'extracting' | 'sending' | 'rendering';

export default function Home() {
  const [inspectionFile, setInspectionFile] = useState<File | null>(null);
  const [thermalFile, setThermalFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<LoadingStep>('idle');
  const [report, setReport] = useState<DDRReport | null>(null);
  const [thermalImages, setThermalImages] = useState<ExtractedImage[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!inspectionFile || !thermalFile) {
      setError('Please upload both PDF files');
      return;
    }

    setError(null);
    setLoading('extracting');

    try {
      const formData = new FormData();
      formData.append('inspectionReport', inspectionFile);
      formData.append('thermalReport', thermalFile);

      setLoading('sending');

      const response = await fetch('/api/generate', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to generate report');
      }

      setLoading('rendering');

      const data = await response.json();
      setReport(data.report);
      setThermalImages(data.images?.thermal || []);
      setLoading('idle');
    } catch (err: any) {
      setError(err.message || 'An error occurred while generating the report');
      setLoading('idle');
    }
  };

  const handleReset = () => {
    setInspectionFile(null);
    setThermalFile(null);
    setReport(null);
    setThermalImages([]);
    setError(null);
    setLoading('idle');
  };

  const canGenerate = inspectionFile && thermalFile && loading === 'idle';

  return (
    <main className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            DDR Report Generator
          </h1>
          <p className="text-gray-600">
            Upload Inspection and Thermal Image Reports to generate a Detailed Diagnostic Report
          </p>
        </div>

        {!report ? (
          /* Upload Interface */
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
              <Uploader
                label="Inspection Report"
                file={inspectionFile}
                onFileChange={setInspectionFile}
                disabled={loading !== 'idle'}
              />

              <Uploader
                label="Thermal Images Report"
                file={thermalFile}
                onFileChange={setThermalFile}
                disabled={loading !== 'idle'}
              />

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                  <p className="font-medium">Error</p>
                  <p className="text-sm mt-1">{error}</p>
                </div>
              )}

              <div className="flex justify-end space-x-4">
                <button
                  onClick={handleGenerate}
                  disabled={!canGenerate}
                  className={`
                    px-6 py-3 rounded-lg font-medium transition-colors
                    ${
                      canGenerate
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    }
                  `}
                >
                  {loading === 'extracting' && 'Extracting PDFs...'}
                  {loading === 'sending' && 'Sending to Gemini...'}
                  {loading === 'rendering' && 'Rendering Report...'}
                  {loading === 'idle' && 'Generate Report'}
                </button>
              </div>

              {loading !== 'idle' && (
                <div className="flex items-center justify-center space-x-2 text-gray-600">
                  <svg
                    className="animate-spin h-5 w-5"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  <span>
                    {loading === 'extracting' && 'Extracting text and images from PDFs...'}
                    {loading === 'sending' && 'Analyzing documents with Gemini AI...'}
                    {loading === 'rendering' && 'Preparing your report...'}
                  </span>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Report Viewer */
          <div>
            <div className="mb-4">
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors flex items-center space-x-2"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 19l-7-7m0 0l7-7m-7 7h18"
                  />
                </svg>
                <span>Upload New Reports</span>
              </button>
            </div>
            <ReportViewer report={report} thermalImages={thermalImages} />
          </div>
        )}
      </div>
    </main>
  );
}

