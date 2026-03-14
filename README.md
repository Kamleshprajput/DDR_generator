# DDR Report Generator - Streamlit Edition

A Python-based web application built with Streamlit that reads two PDF documents (Inspection Report and Thermal Images Report) and generates a structured Detailed Diagnostic Report (DDR) using Google Gemini AI.

## Features

- 📄 PDF text and image extraction using PyPDF2 and pdfplumber
- 🤖 AI-powered report generation using Google Gemini 1.5 Pro
- 🎨 Clean, professional UI with Streamlit
- 📱 Responsive design
- 📥 PDF export functionality using ReportLab
- 📋 JSON export for raw data
- 🔒 Secure API key handling via Streamlit secrets

## Tech Stack

- **Frontend/Backend**: Streamlit (Python)
- **PDF Parsing**: PyPDF2, pdfplumber
- **AI**: Google Gemini 1.5 Pro (via `google-generativeai`)
- **PDF Export**: ReportLab
- **Image Processing**: Pillow (PIL)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

**Option A: Using Streamlit Secrets (Recommended for deployment)**

Create `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
```

**Option B: Using Environment Variable**

```bash
export GEMINI_API_KEY=your_gemini_api_key_here
```

**Option C: Enter in UI**

The app will prompt you to enter the API key in the sidebar if not found.

### 3. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

1. **Upload PDFs**: 
   - Upload the Inspection Report PDF
   - Upload the Thermal Images Report PDF

2. **Generate Report**: 
   - Click "Generate Report" button
   - Wait for processing (extraction → AI analysis → parsing)

3. **View & Export**:
   - Review the generated DDR report
   - Export as PDF using "Export as PDF" button
   - Download JSON using "Copy JSON" button

## Project Structure

```
.
├── app.py                  # Main Streamlit application
├── pdf_extractor.py        # PDF text and image extraction
├── gemini_client.py        # Gemini API integration
├── report_parser.py        # Report parsing utilities
├── requirements.txt        # Python dependencies
├── .streamlit/
│   ├── config.toml         # Streamlit configuration
│   └── secrets.toml.example # Example secrets file
└── README.md               # This file
```

## Deployment to Streamlit Cloud

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: DDR Report Generator"
git remote add origin https://github.com/yourusername/ddr-report-generator.git
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Set main file path: `app.py`
6. Click "Advanced settings"
7. Add secret: `GEMINI_API_KEY` = `your_api_key`
8. Click "Deploy"

### Step 3: Access Your App

Your app will be available at: `https://your-app-name.streamlit.app`

## Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key (required)

## File Size Limits

- Maximum file size: 20MB per PDF
- Streamlit default upload limit: 200MB (configurable)

## Troubleshooting

### PDF Extraction Fails

- Ensure PDFs are valid and not corrupted
- Check file size (max 20MB per file)
- Verify PDFs are not password-protected

### Gemini API Errors

- Verify your `GEMINI_API_KEY` is set correctly
- Check your API key has sufficient quota
- Ensure the model `gemini-1.5-pro` is available in your region
- Check Google Cloud Console for API usage limits

### Image Extraction Issues

- Some PDFs may not have extractable images
- The report will still work with text-only extraction
- Thermal images are matched by page number from the report

### Import Errors

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (3.8+ required)

## API Key Security

- **Never commit API keys to Git**
- Use Streamlit secrets for production deployments
- Use environment variables for local development
- The app will prompt for API key if not found (for testing only)

## License

MIT License

## Support

For issues or questions, please open an issue on GitHub.
