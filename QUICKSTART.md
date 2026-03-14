# Quick Start Guide

## Local Development

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set API Key

Create `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your_api_key_here"
```

Or set environment variable:
```bash
export GEMINI_API_KEY=your_api_key_here
```

### 3. Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add it to your secrets or environment

## Testing

1. Prepare two PDF files:
   - Inspection Report PDF
   - Thermal Images Report PDF

2. Upload both files in the app
3. Click "Generate Report"
4. Wait for processing (may take 30-60 seconds)
5. Review and export the generated report

## Common Issues

### Import Errors
```bash
pip install --upgrade -r requirements.txt
```

### API Key Not Found
- Check `.streamlit/secrets.toml` exists
- Or set `GEMINI_API_KEY` environment variable
- Or enter it in the sidebar when prompted

### PDF Extraction Fails
- Ensure PDFs are valid (not corrupted)
- Check file size (max 20MB)
- Try with different PDF files

## Next Steps

- See `README.md` for full documentation
- See `STREAMLIT_DEPLOY.md` for deployment guide

