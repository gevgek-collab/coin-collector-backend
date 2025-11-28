# Coin Collector Backend API

AI-powered coin information scraper using Groq LLM.

## Features

- 🤖 AI-powered coin data extraction using Groq API
- 🖼️ Intelligent image detection and filtering
- 🛡️ Rate limiting (250 requests/day, 50/hour)
- 📊 Comprehensive logging
- 🔒 Secure API key management via environment variables

## Deployment to Railway

### Prerequisites
- Railway account (https://railway.app)
- Groq API key (https://console.groq.com)

### Step 1: Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo" (or "Empty Project")

### Step 2: Connect Repository

If using GitHub:
1. Connect your GitHub account
2. Select the repository containing this backend
3. Select the branch to deploy

If using Empty Project:
1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Initialize: `railway init`
4. Deploy: `railway up`

### Step 3: Set Environment Variables

In Railway dashboard:
1. Go to your project
2. Click "Variables" tab
3. Add the following variables:

```
GROQ_API_KEY=your_groq_api_key_here
PORT=5000
DEBUG=False
```

⚠️ **IMPORTANT**: Replace `your_groq_api_key_here` with your actual Groq API key!

### Step 4: Deploy

Railway will automatically:
- Detect Python project
- Install dependencies from `requirements.txt`
- Use `Procfile` to start the server
- Assign a public URL

Your backend will be available at: `https://your-app.up.railway.app`

## Local Development

### Setup

1. Create virtual environment:
```bash
python -m venv venv
```

2. Activate virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
```

5. Edit `.env` and add your Groq API key:
```
GROQ_API_KEY=your_actual_api_key_here
```

6. Run the server:
```bash
python app.py
```

Server will start at `http://localhost:5000`

## API Endpoints

### POST /api/scrape

Scrape coin information from URL.

**Request:**
```json
{
  "url": "https://example.com/coin-page"
}
```

**Response:**
```json
{
  "year": "2023",
  "emperor": "Trajan",
  "mint": "Rome",
  "denomination": "Denarius",
  "catalogNumbers": "RIC 123",
  "obverseDescription": "Bust of Trajan...",
  "reverseDescription": "Victory standing...",
  "material": "Silver",
  "diameter": "20",
  "weight": "3.5",
  "grade": "VF",
  "price": "45 EUR",
  "notes": "Additional information...",
  "images": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
  ]
}
```

### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "OK",
  "message": "Backend is running"
}
```

## Rate Limiting

- **Default**: 250 requests per day per IP
- **Hourly**: 50 requests per hour per IP
- **Scrape endpoint**: Additional limit of 10 requests per minute

When rate limit is exceeded, API returns HTTP 429 with:
```json
{
  "error": "Rate limit exceeded",
  "message": "You have exceeded the maximum number of requests. Please try again later."
}
```

## Security

✅ API keys stored in environment variables (not in code)
✅ Rate limiting to prevent abuse
✅ CORS enabled for mobile app access
✅ Comprehensive error handling
✅ Logging for debugging

## Updating Flutter App

After deploying to Railway, update the Flutter app:

1. Get your Railway URL: `https://your-app.up.railway.app`

2. Update `lib/config/environment.dart`:
```dart
static const String scraperApiUrl = String.fromEnvironment(
  'SCRAPER_API_URL',
  defaultValue: 'https://your-app.up.railway.app/api/scrape',
);
```

3. Rebuild the Flutter app

## Monitoring

In Railway dashboard:
- View logs in real-time
- Monitor resource usage
- Set up alerts for errors
- View deployment history

## Troubleshooting

### 500 Internal Server Error
- Check Railway logs
- Verify GROQ_API_KEY is set correctly
- Check if Groq API is responding

### 429 Rate Limit
- User has exceeded request limits
- Wait for rate limit to reset
- Consider increasing limits if needed

### Images not loading
- Check if URLs are accessible
- Verify CORS settings
- Check network connectivity

## License

This backend is part of the Coin Collector app by CollectorsApps.
