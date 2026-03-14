# Vercel Deployment Guide

## Prerequisites

1. A GitHub account
2. A Vercel account (sign up at [vercel.com](https://vercel.com))
3. A Google Gemini API key

## Step-by-Step Deployment

### 1. Push Code to GitHub

```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit: DDR Report Generator with Gemini API"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/yourusername/ddr-report-generator.git
git push -u origin main
```

### 2. Import Project to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "Add New..." → "Project"
3. Import your GitHub repository
4. Vercel will auto-detect Next.js settings

### 3. Configure Environment Variables

1. In the Vercel project settings, go to **Settings** → **Environment Variables**
2. Add the following variable:
   - **Name**: `GEMINI_API_KEY`
   - **Value**: Your Gemini API key
   - **Environment**: Production, Preview, and Development (select all)

3. Click **Save**

### 4. Deploy

1. Click **Deploy** button
2. Vercel will automatically:
   - Install dependencies
   - Build your Next.js app
   - Deploy to production

### 5. Verify Deployment

1. Once deployed, visit your Vercel URL (e.g., `https://your-app.vercel.app`)
2. Test the `/api/health` endpoint: `https://your-app.vercel.app/api/health`
3. Should return: `{"status":"ok"}`

## Configuration Details

### vercel.json

The `vercel.json` file is already configured with:
- Function timeout: 60 seconds (for large PDF processing)
- Environment variable reference for `GEMINI_API_KEY`

### Important Notes

1. **API Key Security**: Never commit your API key to Git. Always use environment variables.

2. **Function Timeout**: The generate route is configured for 60 seconds max duration to handle large PDFs.

3. **File Size Limits**: 
   - Vercel has a 4.5MB limit for serverless functions by default
   - For larger files, consider using Vercel's Pro plan or optimizing PDF sizes

4. **Cold Starts**: First request after inactivity may be slower due to serverless cold starts.

5. **Monitoring**: Check Vercel's dashboard for:
   - Function execution logs
   - Error rates
   - Performance metrics

## Troubleshooting

### Build Fails

- Check build logs in Vercel dashboard
- Ensure all dependencies are in `package.json`
- Verify Node.js version compatibility (should be 18+)

### API Errors

- Verify `GEMINI_API_KEY` is set correctly in Vercel
- Check function logs in Vercel dashboard
- Ensure API key has sufficient quota

### PDF Processing Issues

- Check function timeout settings
- Verify PDF file sizes are under 20MB
- Review error logs for specific issues

## Custom Domain (Optional)

1. Go to **Settings** → **Domains**
2. Add your custom domain
3. Follow DNS configuration instructions
4. SSL certificate is automatically provisioned

## Continuous Deployment

Vercel automatically deploys:
- **Production**: On push to `main` branch
- **Preview**: On push to other branches or pull requests

You can disable auto-deployment in project settings if needed.

