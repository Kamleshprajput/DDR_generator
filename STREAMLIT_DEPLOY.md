# Streamlit Cloud Deployment Guide

## Prerequisites

1. A GitHub account
2. A Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))
3. A Google Gemini API key

## Step-by-Step Deployment

### 1. Prepare Your Repository

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: DDR Report Generator"

# Create GitHub repository, then:
git remote add origin https://github.com/yourusername/ddr-report-generator.git
git push -u origin main
```

**Important**: Make sure `.streamlit/secrets.toml` is in `.gitignore` (it should be by default).

### 2. Deploy on Streamlit Cloud

1. **Sign in to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account
   - Authorize Streamlit to access your repositories

2. **Create New App**
   - Click "New app" button
   - Select your GitHub repository
   - Choose the branch (usually `main` or `master`)
   - Set the main file path: `app.py`

3. **Configure Advanced Settings**
   - Click "Advanced settings"
   - Add your secrets:
     - Click "Secrets" tab
     - Add: `GEMINI_API_KEY` = `your_gemini_api_key_here`
   - Click "Save"

4. **Deploy**
   - Click "Deploy" button
   - Wait for the build to complete (usually 1-2 minutes)

### 3. Access Your App

Once deployed, your app will be available at:
```
https://your-app-name.streamlit.app
```

You can also find the URL in your Streamlit Cloud dashboard.

## Managing Secrets

### Adding/Updating Secrets

1. Go to your app in Streamlit Cloud dashboard
2. Click "Settings" (⚙️ icon)
3. Click "Secrets" tab
4. Edit the secrets file
5. Click "Save"
6. The app will automatically redeploy

### Secrets Format

In Streamlit Cloud, secrets are stored in TOML format:

```toml
GEMINI_API_KEY = "your_api_key_here"
```

## Updating Your App

### Automatic Deployment

Streamlit Cloud automatically redeploys when you push to your main branch:

```bash
git add .
git commit -m "Update app"
git push
```

### Manual Redeploy

1. Go to your app dashboard
2. Click "⋮" (three dots) menu
3. Select "Redeploy"

## Monitoring

### View Logs

1. Go to your app dashboard
2. Click "Manage app"
3. View logs in real-time

### Check Status

- Green dot: App is running
- Yellow dot: App is deploying
- Red dot: App has errors (check logs)

## Troubleshooting

### Build Fails

- Check build logs in Streamlit Cloud dashboard
- Ensure `requirements.txt` is correct
- Verify all dependencies are available on PyPI
- Check Python version compatibility (3.8+)

### App Crashes

- Check runtime logs
- Verify API key is set correctly
- Check for import errors
- Ensure file paths are correct

### API Errors

- Verify `GEMINI_API_KEY` is set in secrets
- Check API key has sufficient quota
- Review error messages in logs

### File Upload Issues

- Check file size limits (default 200MB on Streamlit Cloud)
- Verify PDF files are valid
- Check upload timeout settings

## Custom Domain (Optional)

Streamlit Cloud doesn't support custom domains on the free tier. For custom domains, consider:
- Streamlit Cloud for Teams (paid)
- Self-hosting on your own server
- Using a reverse proxy

## Resource Limits

### Free Tier

- 1 app per account
- Public apps only
- Standard compute resources
- 1GB RAM
- Shared CPU

### Team Tier (Paid)

- Multiple apps
- Private apps
- More compute resources
- Priority support

## Best Practices

1. **Never commit secrets**: Always use Streamlit secrets
2. **Test locally first**: Run `streamlit run app.py` before deploying
3. **Monitor usage**: Check API quotas regularly
4. **Error handling**: Add proper error messages for users
5. **File validation**: Validate file types and sizes
6. **Rate limiting**: Consider rate limiting for API calls

## Security

- API keys are encrypted in Streamlit Cloud
- Secrets are only accessible to your app
- Use HTTPS (automatic on Streamlit Cloud)
- Never log sensitive information

## Support

- Streamlit Community: [discuss.streamlit.io](https://discuss.streamlit.io)
- Streamlit Docs: [docs.streamlit.io](https://docs.streamlit.io)
- GitHub Issues: Open an issue in your repository

