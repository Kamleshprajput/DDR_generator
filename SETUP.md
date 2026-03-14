# Setup Guide

## Prerequisites

- Node.js 18+ installed
- An Anthropic API key

## Installation Steps

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Create environment file:**
   Create a `.env.local` file in the root directory:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```

4. **Open your browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Usage

1. Upload two PDF files:
   - **Inspection Report**: The main inspection document
   - **Thermal Images Report**: The thermal imaging report

2. Click "Generate Report" and wait for processing:
   - PDFs are extracted (text + images)
   - Documents are sent to Claude AI for analysis
   - Report is generated and displayed

3. View and export:
   - Review the generated DDR report
   - Export as PDF using the "Export as PDF" button
   - Copy the raw JSON using the "Copy JSON" button

## Health Check

Test the API health endpoint:
```bash
curl http://localhost:3000/api/health
```

Should return: `{"status":"ok"}`

## Troubleshooting

### PDF extraction fails
- Ensure PDFs are valid and not corrupted
- Check file size (max 20MB per file)
- Verify PDFs are not password-protected

### Gemini API errors
- Verify your `GEMINI_API_KEY` is set correctly
- Check your API key has sufficient credits/quota
- Ensure the model `gemini-1.5-pro` is available in your region
- Check Google Cloud Console for API usage limits

### Image extraction issues
- Some PDFs may not have extractable images
- The report will still work with text-only extraction
- Thermal images are matched by page number from the report

## Production Deployment

1. Set environment variables in your hosting platform
2. Build the application:
   ```bash
   npm run build
   ```
3. Start the production server:
   ```bash
   npm start
   ```

## Notes

- API keys are never exposed to the frontend
- All Claude API calls happen server-side
- Large PDFs (>20MB) will be rejected
- Processing time depends on PDF size and complexity

