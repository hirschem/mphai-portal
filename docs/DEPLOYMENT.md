# MPH Handwriting Pipeline - Vercel Deployment

## Frontend Deployment (mphai.app)

### Option 1: Vercel CLI (Recommended)

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Deploy:**
   ```bash
   cd apps/web
   vercel
   ```

3. **Configure domain:**
   - In Vercel dashboard, go to Project Settings → Domains
   - Add `mphai.app` and `www.mphai.app`

### Option 2: Vercel GitHub Integration

1. Push this repo to GitHub
2. Connect GitHub repo to Vercel
3. Vercel auto-detects Next.js and deploys
4. Add custom domain: `mphai.app`

## Backend Deployment

The backend needs to be deployed separately. Options:

### Option 1: Railway (Easiest for FastAPI)

1. **Deploy to Railway:**
   ```bash
   railway login
   railway init
   railway up
   ```

2. **Set environment variables in Railway dashboard:**
   - `OPENAI_API_KEY`: Your OpenAI key

3. **Get Railway URL** (e.g., `https://mph-api.railway.app`)

4. **Update Vercel environment:**
   - Set `NEXT_PUBLIC_API_URL` to your Railway URL

### Option 2: Render

1. Create new Web Service on Render
2. Connect GitHub repo
3. Root directory: `apps/api`
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variable: `OPENAI_API_KEY`

### Option 3: AWS/DigitalOcean (Full Control)

Deploy with Docker - configuration files ready in repo.

## Post-Deployment Setup

1. Update `NEXT_PUBLIC_API_URL` in Vercel to point to deployed backend
2. Configure CORS in backend to allow `mphai.app`
3. Test with real proposal images
4. Monitor OpenAI API usage

## Local Testing Before Deploy

1. Add OpenAI key to `.env`
2. Start backend: `cd apps/api && uvicorn app.main:app --reload`
3. Start frontend: `cd apps/web && npm run dev`
4. Test at `http://localhost:3000`
