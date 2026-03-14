import { NextRequest, NextResponse } from 'next/server';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { extractPdf } from '@/lib/extractPdf';
import { buildUserPrompt, SYSTEM_PROMPT } from '@/lib/buildPrompt';
import { parseReport } from '@/lib/parseReport';

// Configure route for large file uploads
export const runtime = 'nodejs';
export const maxDuration = 60; // 60 seconds

const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20MB

export async function POST(request: NextRequest) {
  try {
    const apiKey = process.env.GEMINI_API_KEY;
    
    if (!apiKey) {
      return NextResponse.json(
        { error: 'GEMINI_API_KEY is not configured' },
        { status: 500 }
      );
    }

    const formData = await request.formData();
    const inspectionFile = formData.get('inspectionReport') as File | null;
    const thermalFile = formData.get('thermalReport') as File | null;

    if (!inspectionFile || !thermalFile) {
      return NextResponse.json(
        { error: 'Both inspection report and thermal report are required' },
        { status: 400 }
      );
    }

    // Validate file types
    if (inspectionFile.type !== 'application/pdf' || thermalFile.type !== 'application/pdf') {
      return NextResponse.json(
        { error: 'Both files must be PDF documents' },
        { status: 400 }
      );
    }

    // Check file sizes
    if (inspectionFile.size > MAX_FILE_SIZE || thermalFile.size > MAX_FILE_SIZE) {
      return NextResponse.json(
        { error: 'File size must be less than 20MB' },
        { status: 400 }
      );
    }

    // Extract text and images from both PDFs
    const [inspectionData, thermalData] = await Promise.all([
      extractPdf(inspectionFile),
      extractPdf(thermalFile),
    ]);

    // Convert PDFs to base64 for Gemini
    const inspectionArrayBuffer = await inspectionFile.arrayBuffer();
    const thermalArrayBuffer = await thermalFile.arrayBuffer();
    
    const inspectionBase64 = Buffer.from(inspectionArrayBuffer).toString('base64');
    const thermalBase64 = Buffer.from(thermalArrayBuffer).toString('base64');

    // Initialize Gemini client
    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel({ 
      model: 'gemini-1.5-pro',
      systemInstruction: SYSTEM_PROMPT,
    });

    // Build the user prompt with extracted text
    const userPrompt = buildUserPrompt(
      inspectionData.text,
      thermalData.text
    );

    // Prepare content parts for Gemini
    const parts = [
      { text: userPrompt },
      {
        inlineData: {
          data: inspectionBase64,
          mimeType: 'application/pdf',
        },
      },
      {
        inlineData: {
          data: thermalBase64,
          mimeType: 'application/pdf',
        },
      },
    ];

    // Call Gemini API
    const result = await model.generateContent(parts);

    const response = result.response;
    const responseText = response.text();

    if (!responseText) {
      throw new Error('Gemini API returned no text content');
    }

    // Parse the JSON response
    const report = parseReport(responseText);

    // Return the report along with image data for rendering
    return NextResponse.json({
      report,
      images: {
        inspection: inspectionData.images,
        thermal: thermalData.images,
      },
    });
  } catch (error: any) {
    console.error('Error generating report:', error);
    
    return NextResponse.json(
      { 
        error: error.message || 'Failed to generate report',
        details: error.toString(),
      },
      { status: 500 }
    );
  }
}

