# Deploying MPH Handwriting to Production

## Step 1: Deploy Backend to Railway (5 minutes)

### Why Railway?
- Free tier available
- Perfect for FastAPI
- Automatic HTTPS
- Dead simple setup

### Deploy Backend:

1. **Go to [Railway.app](https://railway.app)**
   - Sign up with GitHub

2. **Create New Project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your GitHub account
   - Select your repo

3. **Configure the service:**
   - Root directory: `apps/api`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables:**
   - Go to Variables tab
   - Add: `OPENAI_API_KEY` = `your_key_here`

5. **Get your backend URL:**
   - Railway will give you a URL like: `https://mph-api.railway.app`
   - Copy this URL!

## Step 2: Deploy Frontend to Vercel (3 minutes)

### Deploy to Vercel:

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Deploy from the web folder:**
   ```bash
   cd apps/web
   vercel --prod
   ```

3. **During deployment, answer:**
   - Set up and deploy: **Y**
   - Which scope: Choose your account
   - Link to existing project: **N**
   - Project name: **mph-handwriting**
   - Directory: **.**  (current directory)
   - Override settings: **N**

4. **Add environment variable:**
   - When prompted or in Vercel dashboard:
   - `NEXT_PUBLIC_API_URL` = `https://your-railway-url.railway.app`

## Step 3: Connect Custom Domain (mphai.app)

### In Vercel Dashboard:

1. Go to your project settings
2. Click "Domains"
3. Add domain: `mphai.app`
4. Add domain: `www.mphai.app`

### Update DNS (at your domain registrar):

Add these records:

**A Record:**
- Type: `A`
- Name: `@`
- Value: `76.76.21.21`

**CNAME Record:**
- Type: `CNAME`
- Name: `www`
- Value: `cname.vercel-dns.com`

Vercel will automatically provision SSL certificate.

## Step 4: Update Backend CORS

Make sure your Railway backend URL is in the CORS settings (already done in code).

## Done! 🎉

Your app will be live at:
- **https://mphai.app** - Your production app
- Backend API: Your Railway URL

---

## Alternative: Quick Deploy Script

Run this from the project root:

```bash
# Deploy frontend
cd apps/web
vercel --prod

# Note the URL, then update your Railway environment variables
```
