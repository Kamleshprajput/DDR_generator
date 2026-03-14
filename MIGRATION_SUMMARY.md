# Migration Summary: Claude → Gemini API

## Changes Made

### 1. Package Dependencies
- ✅ Removed: `@anthropic-ai/sdk`
- ✅ Added: `@google/generative-ai`

### 2. API Integration (`app/api/generate/route.ts`)
- ✅ Replaced Anthropic client with GoogleGenerativeAI
- ✅ Updated model from `claude-sonnet-4-20250514` to `gemini-1.5-pro`
- ✅ Changed API call format to Gemini's `generateContent()` method
- ✅ Updated PDF attachment format to use `inlineData` with `mimeType`

### 3. Environment Variables
- ✅ Changed from `ANTHROPIC_API_KEY` to `GEMINI_API_KEY`
- ✅ Updated all references in code and documentation

### 4. UI Updates
- ✅ Updated loading messages from "Claude" to "Gemini"
- ✅ Updated user-facing text references

### 5. Documentation
- ✅ Updated README.md
- ✅ Updated SETUP.md
- ✅ Created VERCEL_DEPLOY.md
- ✅ Created this migration summary

### 6. Vercel Configuration
- ✅ Created `vercel.json` with function timeout settings
- ✅ Configured for 60-second max duration for PDF processing

## Next Steps

1. **Install new dependencies:**
   ```bash
   npm install
   ```

2. **Update environment variable:**
   - Create/update `.env.local`:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

3. **Get Gemini API Key:**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy it to your `.env.local` file

4. **Test locally:**
   ```bash
   npm run dev
   ```

5. **Deploy to Vercel:**
   - Follow instructions in `VERCEL_DEPLOY.md`
   - Add `GEMINI_API_KEY` in Vercel dashboard
   - Deploy!

## Key Differences: Claude vs Gemini

| Feature | Claude | Gemini |
|---------|--------|--------|
| SDK Package | `@anthropic-ai/sdk` | `@google/generative-ai` |
| Model Name | `claude-sonnet-4-20250514` | `gemini-1.5-pro` |
| PDF Format | `type: 'image', source: { type: 'base64', media_type: 'application/pdf' }` | `inlineData: { data: base64, mimeType: 'application/pdf' }` |
| System Instructions | `system` parameter | `systemInstruction` in model config |
| API Call | `messages.create()` | `generateContent()` |

## Notes

- The system prompt and JSON structure remain the same
- PDF extraction logic is unchanged
- Report parsing logic is unchanged
- All UI components work the same way

## Testing Checklist

- [ ] Install dependencies successfully
- [ ] Set GEMINI_API_KEY environment variable
- [ ] Test PDF upload locally
- [ ] Verify report generation works
- [ ] Test health endpoint
- [ ] Deploy to Vercel
- [ ] Add environment variable in Vercel
- [ ] Test deployed application

