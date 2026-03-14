'use client';

import { useRef, useState } from 'react';
import { DDRReport } from '@/lib/parseReport';
import { ExtractedImage } from '@/lib/extractPdf';

interface ReportViewerProps {
  report: DDRReport;
  thermalImages: ExtractedImage[];
}

const severityColors = {
  Critical: 'bg-red-100 text-red-800 border-red-300',
  High: 'bg-orange-100 text-orange-800 border-orange-300',
  Medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  Low: 'bg-green-100 text-green-800 border-green-300',
};

export default function ReportViewer({ report, thermalImages }: ReportViewerProps) {
  const reportRef = useRef<HTMLDivElement>(null);
  const [copySuccess, setCopySuccess] = useState(false);

  const exportToPdf = async () => {
    if (!reportRef.current) return;

    // Dynamically import html2pdf.js (client-side only)
    const html2pdf = (await import('html2pdf.js')).default;

    const element = reportRef.current;
    const opt = {
      margin: 1,
      filename: `DDR_Report_${new Date().toISOString().split('T')[0]}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' },
    };

    html2pdf().set(opt).from(element).save();
  };

  const copyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(report, null, 2));
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  const getThermalImage = (pageNum: number | null): ExtractedImage | null => {
    if (pageNum === null) return null;
    return thermalImages.find(img => img.pageNum === pageNum) || null;
  };

  return (
    <div className="w-full max-w-6xl mx-auto">
      {/* Action Buttons */}
      <div className="mb-6 flex flex-wrap gap-3 justify-end">
        <button
          onClick={exportToPdf}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
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
              d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <span>Export as PDF</span>
        </button>
        <button
          onClick={copyJson}
          className={`px-4 py-2 border rounded-lg transition-colors flex items-center space-x-2 ${
            copySuccess
              ? 'bg-green-50 border-green-300 text-green-700'
              : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
          }`}
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
              d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
            />
          </svg>
          <span>{copySuccess ? 'Copied!' : 'Copy JSON'}</span>
        </button>
      </div>

      {/* Report Content */}
      <div
        ref={reportRef}
        className="bg-white shadow-lg rounded-lg p-8 space-y-8"
      >
        {/* Header */}
        <div className="border-b-2 border-gray-200 pb-4">
          <h1 className="text-3xl font-bold text-gray-900">
            Detailed Diagnostic Report (DDR)
          </h1>
          <p className="text-sm text-gray-500 mt-2">
            Generated on {new Date().toLocaleDateString()}
          </p>
        </div>

        {/* Property Summary */}
        <section>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            Property Summary
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg">
            <div>
              <span className="text-sm font-medium text-gray-600">Property Type:</span>
              <p className="text-gray-900">{report.property_summary.property_type}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">Floors:</span>
              <p className="text-gray-900">{report.property_summary.floors}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">Inspection Date:</span>
              <p className="text-gray-900">{report.property_summary.inspection_date}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">Inspected By:</span>
              <p className="text-gray-900">{report.property_summary.inspected_by}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">Customer Name:</span>
              <p className="text-gray-900">{report.property_summary.customer_name}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">Address:</span>
              <p className="text-gray-900">{report.property_summary.address}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">Previous Audit:</span>
              <p className="text-gray-900">{report.property_summary.previous_audit}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">Previous Repair:</span>
              <p className="text-gray-900">{report.property_summary.previous_repair}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">Overall Score:</span>
              <p className="text-gray-900">{report.property_summary.overall_score}</p>
            </div>
          </div>
          <div className="mt-4">
            <span className="text-sm font-medium text-gray-600">Overview:</span>
            <p className="text-gray-900 mt-1">{report.property_summary.overview}</p>
          </div>
        </section>

        {/* Severity */}
        <section>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            Severity Assessment
          </h2>
          <div className="flex items-start space-x-4">
            <span
              className={`px-4 py-2 rounded-lg border font-semibold ${
                severityColors[report.severity.level]
              }`}
            >
              {report.severity.level}
            </span>
            <p className="text-gray-700 flex-1">{report.severity.reasoning}</p>
          </div>
        </section>

        {/* Area Observations */}
        <section>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            Area Observations
          </h2>
          <div className="space-y-6">
            {report.area_observations.map((observation, index) => {
              const thermalImage = getThermalImage(observation.thermal_image_page);
              return (
                <div
                  key={index}
                  className="border border-gray-200 rounded-lg p-6 bg-gray-50"
                >
                  <h3 className="text-xl font-semibold text-gray-800 mb-4">
                    {observation.area}
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <span className="text-sm font-medium text-gray-600">
                        Negative Side (Interior):
                      </span>
                      <p className="text-gray-900 mt-1">{observation.negative_side}</p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-600">
                        Positive Side (Exterior):
                      </span>
                      <p className="text-gray-900 mt-1">{observation.positive_side}</p>
                    </div>
                  </div>
                  <div className="mb-4">
                    <span className="text-sm font-medium text-gray-600">
                      Thermal Data:
                    </span>
                    <p className="text-gray-900 mt-1">{observation.thermal_data}</p>
                  </div>
                  {thermalImage && (
                    <div className="mt-4">
                      <span className="text-sm font-medium text-gray-600 block mb-2">
                        Thermal Image (Page {observation.thermal_image_page}):
                      </span>
                      <img
                        src={`data:${thermalImage.mimeType};base64,${thermalImage.base64}`}
                        alt={`Thermal image for ${observation.area}`}
                        className="max-w-full h-auto rounded-lg border border-gray-300"
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* Root Causes */}
        <section>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            Root Causes
          </h2>
          <ul className="list-disc list-inside space-y-2 text-gray-700">
            {report.root_causes.map((cause, index) => (
              <li key={index}>{cause}</li>
            ))}
          </ul>
        </section>

        {/* Recommended Actions */}
        <section>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            Recommended Actions
          </h2>
          <ul className="list-disc list-inside space-y-2 text-gray-700">
            {report.recommended_actions.map((action, index) => (
              <li key={index}>{action}</li>
            ))}
          </ul>
        </section>

        {/* Additional Notes */}
        {report.additional_notes !== 'Not Available' && (
          <section>
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">
              Additional Notes
            </h2>
            <p className="text-gray-700">{report.additional_notes}</p>
          </section>
        )}

        {/* Missing Information */}
        {report.missing_information.length > 0 && (
          <section>
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">
              Missing Information
            </h2>
            <ul className="list-disc list-inside space-y-2 text-gray-700">
              {report.missing_information.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </div>
  );
}

