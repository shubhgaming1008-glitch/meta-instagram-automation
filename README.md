<div align="center">
  <img src="https://via.placeholder.com/150?text=Logo" alt="Logo" width="150" height="150">

  # 🚀 Instagram DM Automation Platform

  **Your personal assistant for Instagram DMs, Comments, and Stories!**<br>
  I built this platform to help creators and businesses automate their Instagram interactions without losing that personal touch. It uses the official Meta Graph API to auto-reply to comments, story mentions, and DMs.

  <p align="center">
    <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI">
    <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React">
    <img src="https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript">
    <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
    <img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white" alt="Celery">
  </p>
  
  <br/>
  
  <img src="assets/1.png" alt="App Screenshot 1" width="800" style="border-radius: 12px; margin-bottom: 20px;">
  <br/>
  <img src="assets/2.png" alt="App Screenshot 2" width="800" style="border-radius: 12px; margin-bottom: 20px;">
  <br/>
  <img src="assets/3.png" alt="App Screenshot 3" width="800" style="border-radius: 12px; margin-bottom: 20px;">
  
</div>

<br/>

## ✨ Why I Built This (Features)

I got tired of manually replying to every single "Link please!" comment. So, I built this visual flow builder to do the heavy lifting:

- 🎨 **Drag-and-Drop Flow Builder**: Creating conversation flows is as easy as drawing a flowchart.
- ⚡ **Trigger Engine**:
  - 💬 **Comment Replies**: Someone comments a specific word? Boom, they get an auto-reply and a DM instantly.
  - 📖 **Story Mentions**: Automatically thank your followers when they tag you in their stories.
  - ✉️ **Keyword DMs**: Trigger full conversation funnels based on DM keywords.
- 📬 **Unified Inbox**: I added a CRM-like inbox so you can manage all your automated and manual chats in one clean dashboard.
- 🔗 **Link Management**: Generate short links and see exactly which campaigns are driving clicks.
- 👥 **Audience Database**: The system automatically saves everyone who interacts with you into a clean contact list.

---

## 🛠️ How It Works (The Workflow)

Using the platform is extremely straightforward. Here is exactly how it automates your Instagram:

1. **🔗 Connect Meta OAuth**: You log in with Facebook and select the Instagram Business account you want to automate. The system securely saves your tokens using Fernet encryption.
2. **🏗️ Build a Flow**: Head over to the **Flow Builder**. It’s a node-based visual canvas. You can drag and drop different "Blocks":
   - **Trigger Block**: When a user comments "PRICE", start the flow.
   - **Action Block**: Send them a DM saying "Here is the price list!".
   - **Condition Block**: (Coming Soon) Check if they are actually following you before sending the link!
3. **🚀 Go Live**: Once you activate the automation, the backend registers Webhooks with Meta.
4. **🤖 Automation in Action**: When a user comments on your Reel, Meta sends a webhook to the FastAPI backend. Celery picks up the task, matches the keyword, and instantly fires back a DM using the Graph API.
5. **📈 Track Analytics**: Every single message sent, opened, and link clicked is logged. You can see real-time charts in your Dashboard.

---

## 🛠 What's Under the Hood?

I wanted this to be fast and scale easily, so here is the tech stack:

### ⚙️ Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Because Python + Speed = ❤️)
- **Database**: PostgreSQL (I use [Neon](https://neon.tech/) for serverless Postgres)
- **Task Queue**: Celery + Redis (Handles the heavy background tasks like sending messages)
- **Security**: JWT for auth and Fernet encryption for keeping Meta API tokens safe.

### 💻 Frontend
- **Framework**: [React](https://reactjs.org/) + [Vite](https://vitejs.dev/) + TypeScript
- **Styling**: Tailwind CSS (With some Framer Motion for smooth animations)
- **State**: Zustand (Because Redux was too much boilerplate)

---

## 🚀 How to Run It Locally

Want to tinker with the code? Here's how to get it running on your machine:

### Prerequisites
Make sure you have Node.js (v18+), Python (3.9+), a PostgreSQL database, and Redis installed.

### 1. Clone the Repo
```bash
git clone https://github.com/yourusername/instagram-dm-automation.git
cd instagram-dm-automation
```

### 2. Set Up the Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Rename `.env.example` to `.env` and fill in your details:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

SECRET_KEY=your_secret_key
ENCRYPTION_KEY=your_fernet_key

META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret
FRONTEND_URL=http://localhost:5173
```

Fire it up:
```bash
uvicorn app.main:app --reload --port 8000
# In a new terminal, start Celery:
celery -A app.core.celery_app worker --loglevel=info
```

### 3. Set Up the Frontend
```bash
cd frontend
npm install
```

Create a `.env` file in the frontend folder:
```env
VITE_API_URL=http://localhost:8000
VITE_META_APP_ID=your_meta_app_id
```

Run the dev server:
```bash
npm run dev
```

---

## 🌍 How to Deploy It

If you want to put this on the internet, here is my recommended setup:

- **Backend**: Deploy on [Render](https://render.com/) or Railway. Just connect the repo, set the build command to `pip install -r requirements.txt`, and the start command to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Don't forget to spin up a background worker for Celery!
- **Frontend**: Deploy on [Vercel](https://vercel.com/) or Netlify. Super easy, just select Vite as the preset.
- **Database/Redis**: I highly recommend Neon for Postgres and Upstash for Redis.

---

## 💖 Support the Project

I spent countless nights coding this platform and reverse-engineering the Meta API so you don't have to! If this project helped you save time, get more leads, or you just want to say thanks, I would incredibly appreciate your support. 

<a href="#" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 50px !important;width: 180px !important;" >
</a>

Star the repo ⭐, share it with your friends, or feel free to open a PR if you want to contribute!

---

<div align="center">
  <p>Made with ❤️ by a developer who hates repetitive tasks.</p>
</div>
