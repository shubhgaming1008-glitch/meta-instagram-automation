<div align="center">
  <img src="https://via.placeholder.com/150?text=Logo" alt="Logo" width="150" height="150">

  # 🚀 Instagram DM Automation Platform

  **A full-stack, enterprise-grade Instagram Direct Message automation platform.**<br>
  Build conversational flows, track analytics, manage leads, and automatically reply to comments, story mentions, and DMs using the official Meta Graph API.

  <p align="center">
    <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI">
    <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React">
    <img src="https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript">
    <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
    <img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white" alt="Celery">
  </p>
</div>

<br/>

## ✨ Features

- 🎨 **Visual Flow Builder**: Create complex, multi-step conversation flows visually.
- ⚡ **Trigger Engine**:
  - 💬 **Comment Replies**: Auto-reply and auto-DM when someone comments on your posts/reels.
  - 📖 **Story Mentions**: Instantly thank or engage with users who mention you in their stories.
  - ✉️ **Keyword DMs**: Trigger specific flows based on keywords sent in direct messages.
- 📬 **Unified Inbox**: Manage all your Instagram DMs from a beautiful, CRM-like interface.
- 🔗 **Link Management**: Generate trackable short links to measure campaign effectiveness.
- 👥 **Audience & Contacts**: Automatically build a lead database from user interactions.
- 📊 **Analytics & Logs**: Detailed insights into automation performance and system health.

---

## 🛠 Tech Stack

### ⚙️ Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Database**: PostgreSQL (via [Neon](https://neon.tech/)) + SQLAlchemy ORM
- **Task Queue**: Celery + Redis (for background message processing)
- **Authentication**: JWT & Meta OAuth
- **Security**: Fernet encryption for API tokens

### 💻 Frontend
- **Framework**: [React](https://reactjs.org/) + [Vite](https://vitejs.dev/) + TypeScript
- **Styling**: Tailwind CSS + Framer Motion
- **State Management**: Zustand
- **Icons**: Lucide React

---

## 🚀 Getting Started (Local Development)

### Prerequisites
- `Node.js` (v18+)
- `Python` (3.9+)
- `PostgreSQL` Database (Local or Neon)
- `Redis` Server (Local or Upstash)
- `Meta Developer Account` (for Instagram Graph API)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/instagram-dm-automation.git
cd instagram-dm-automation
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend` directory based on `.env.example`:
```env
# Backend .env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

SECRET_KEY=generate_a_secure_random_string_here
ENCRYPTION_KEY=generate_a_url_safe_base64_key_here

META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_WEBHOOK_VERIFY_TOKEN=your_custom_webhook_verify_token

FRONTEND_URL=http://localhost:5173
```

Run the backend servers:
```bash
# Terminal 1: FastAPI Server
uvicorn app.main:app --reload --port 8000

# Terminal 2: Celery Worker
celery -A app.core.celery_app worker --loglevel=info
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

Create a `.env` file in the `frontend` directory:
```env
VITE_API_URL=http://localhost:8000
VITE_META_APP_ID=your_meta_app_id
```

Run the frontend dev server:
```bash
npm run dev
```

---

## 🌍 Deployment Guide

This application is designed to be easily deployed on modern cloud platforms.

### ☁️ Backend Deployment (Recommended: Render / Railway)

1. Connect your GitHub repository to [Render](https://render.com/).
2. Create a new **Web Service**.
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add all your environment variables (`DATABASE_URL`, `REDIS_URL`, `META_APP_ID`, etc.) in the Render dashboard.
6. Create a **Background Worker** on Render for Celery:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `celery -A app.core.celery_app worker --loglevel=info`

### 🌐 Frontend Deployment (Recommended: Vercel / Netlify)

1. Connect your GitHub repository to [Vercel](https://vercel.com/).
2. Framework Preset: `Vite`
3. Root Directory: `frontend`
4. Build Command: `npm run build`
5. Output Directory: `dist`
6. Add your Environment Variables:
   - `VITE_API_URL`: Your deployed backend URL (e.g., `https://my-backend.onrender.com`)
   - `VITE_META_APP_ID`: Your Meta App ID
7. Deploy!

---

## 🔒 Meta App Configuration

To use this app, you must configure a Meta Developer App:
1. Create a Business App on [Meta for Developers](https://developers.facebook.com/).
2. Add the **Instagram Graph API** and **Facebook Login for Business** products.
3. Configure the **OAuth Redirect URI** to `https://your-backend.com/api/instagram/oauth/callback`.
4. Configure **Webhooks**:
   - Callback URL: `https://your-backend.com/api/instagram/webhook`
   - Verify Token: The `META_WEBHOOK_VERIFY_TOKEN` from your `.env`.
   - Subscribed Fields: `messages`, `messaging_postbacks`, `comments`, `message_reactions`.
5. Request Advanced Access for: `instagram_basic`, `instagram_manage_messages`, `instagram_manage_comments`, `pages_show_list`, `pages_read_engagement`, `pages_manage_metadata`.

---

<div align="center">
  <p>Made with ❤️ for Instagram Automation</p>
</div>
