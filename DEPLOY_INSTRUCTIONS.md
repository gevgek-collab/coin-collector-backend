# Railway Deployment Instructions

## Option 1: Via Railway CLI (Recommended)

### Step 1: Install Railway CLI

Open PowerShell/Command Prompt and run:
```bash
npm install -g @railway/cli
```

If you don't have npm, install Node.js first from: https://nodejs.org/

### Step 2: Login to Railway

```bash
railway login
```

This will open a browser window - login with your Railway account.

### Step 3: Initialize Project

Navigate to backend directory:
```bash
cd C:\CoinCollectorBackend
```

Initialize Railway project:
```bash
railway init
```

When prompted:
- Project name: `coin-collector-backend`
- Select: "Create new project"

### Step 4: Set Environment Variables

Set your Groq API key:
```bash
railway variables set GROQ_API_KEY=your_groq_api_key_here
```

### Step 5: Deploy

Deploy the backend:
```bash
railway up
```

Wait for deployment to complete (1-2 minutes).

### Step 6: Get Your URL

Get the public URL:
```bash
railway open
```

Or view deployment details:
```bash
railway status
```

Your backend URL will be something like: `https://coin-collector-backend-production.up.railway.app`

---

## Option 2: Via Railway Web Dashboard

### Step 1: Create New Project

1. Go to: https://railway.app/dashboard
2. Click "New Project"
3. Select "Empty Project"
4. Name it: `coin-collector-backend`

### Step 2: Deploy from Local Files

1. Click "Deploy from GitHub repo" or "Empty Service"
2. If using GitHub:
   - Push your backend code to GitHub
   - Connect the repository
   - Select the branch
3. If using local files:
   - Install Railway CLI (see Option 1)
   - Use `railway up` command

### Step 3: Set Environment Variables

1. In your project, click "Variables" tab
2. Click "New Variable"
3. Add:
   - Key: `GROQ_API_KEY`
   - Value: `your_groq_api_key_here`
4. Click "Add"

### Step 4: Enable Public Access

1. Click "Settings" tab
2. Scroll to "Networking"
3. Click "Generate Domain"
4. Your public URL will be generated (e.g., `https://your-app.up.railway.app`)

### Step 5: Verify Deployment

Test the health endpoint:
```
https://your-app.up.railway.app/api/health
```

Should return:
```json
{
  "status": "OK",
  "message": "Backend is running"
}
```

---

## Troubleshooting

### Deployment Failed

Check logs:
```bash
railway logs
```

Common issues:
- Missing dependencies: Check `requirements.txt`
- Port not set: Railway should auto-detect from Procfile
- Environment variables: Verify GROQ_API_KEY is set

### API Key Not Working

Verify environment variable:
```bash
railway variables
```

Should show:
```
GROQ_API_KEY = gsk_fH7zM...
```

### App Not Starting

Check Procfile:
```
web: gunicorn app:app
```

Check runtime.txt:
```
python-3.11.6
```

---

## Next Steps After Deployment

1. Copy your Railway URL (e.g., `https://your-app.up.railway.app`)

2. Update Flutter app `lib/config/environment.dart`:
```dart
static const String scraperApiUrl = String.fromEnvironment(
  'SCRAPER_API_URL',
  defaultValue: 'https://your-app.up.railway.app/api/scrape',
);
```

3. Test the API from Flutter app or Postman:
```
POST https://your-app.up.railway.app/api/scrape
Body: {"url": "https://example.com/coin-page"}
```

4. Monitor usage in Railway dashboard

---

## Monitoring & Maintenance

### View Logs
```bash
railway logs --follow
```

### Check Status
```bash
railway status
```

### Redeploy
```bash
railway up
```

### Update Environment Variables
```bash
railway variables set KEY=VALUE
```

---

## Cost

Railway Free Tier includes:
- $5 free credit per month
- ~500 hours of usage
- More than enough for development/testing

For production with heavy usage, consider upgrading to Pro plan.
