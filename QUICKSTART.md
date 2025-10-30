# ⚡ Quick Start Guide (5 Minutes)

Get the platform running in 5 minutes with Docker!

---

## 📋 Prerequisites

1. **Install Docker Desktop**: https://www.docker.com/products/docker-desktop/
   - Windows/Mac: Download and install
   - Linux: Follow instructions for your distro

2. **Install Node.js**: https://nodejs.org/ (LTS version)

3. **Get OpenAI API Key**: https://platform.openai.com/api-keys
   - Sign up for OpenAI account
   - Create a new API key
   - Copy the key (starts with `sk-...`)

---

## 🚀 Installation Steps

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Suhas2609/Misconception-driven-STEM-question-generation-platform.git
cd Misconception-driven-STEM-question-generation-platform
```

### 2️⃣ Configure Environment

```bash
cd misconception_stem_rag
```

**Windows PowerShell**:
```powershell
Copy-Item .env.example .env
notepad .env
```

**macOS/Linux**:
```bash
cp .env.example .env
nano .env
```

**Edit the `.env` file and add your OpenAI API key**:
```env
OPENAI_API_KEY=sk-your-actual-key-here    # ← Replace this!
```

Save and close the file.

### 3️⃣ Start Backend Services

```bash
# Make sure you're in misconception_stem_rag directory
docker-compose up -d
```

Wait ~30 seconds for all services to start. Check status:
```bash
docker-compose ps
```

You should see 4 services running:
- ✅ adaptive_api
- ✅ mongo
- ✅ redis  
- ✅ chroma

### 4️⃣ Start Frontend

Open a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

---

## ✅ Access the Application

**🌐 Frontend**: http://localhost:5173  
**🔧 Backend API**: http://localhost:8000/docs

---

## 🎯 First Use

1. **Register**: Create your account at http://localhost:5173
2. **Onboarding**: Complete the 5-question assessment
3. **Upload PDF**: Upload a STEM textbook or notes
4. **Take Quiz**: Select topics and start learning!

---

## 🛑 Stopping the Application

```bash
# Stop frontend: Press Ctrl+C in the terminal

# Stop backend:
cd misconception_stem_rag
docker-compose down
```

---

## 🔄 Restarting

```bash
# Terminal 1 - Backend
cd misconception_stem_rag
docker-compose up -d

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

---

## ❗ Common Issues

### Docker won't start
- ✅ Make sure Docker Desktop is running
- ✅ Try: `docker-compose down` then `docker-compose up -d`

### Can't access frontend
- ✅ Check if `npm run dev` is running
- ✅ Try: `npm install` then `npm run dev`

### API key errors
- ✅ Check `.env` file has your correct OpenAI API key
- ✅ No spaces around the `=` sign
- ✅ Restart: `docker-compose restart api`

### Port already in use
**Backend (8000)**:
```bash
docker-compose down
docker-compose up -d
```

**Frontend (5173)**:
```bash
npm run dev -- --port 3000
```

---

## 📚 Full Documentation

For detailed installation instructions, troubleshooting, and manual setup:
- See **[INSTALLATION.md](./INSTALLATION.md)**

---

## 🎉 That's It!

You're ready to use the adaptive learning platform! 

Visit http://localhost:5173 to get started.
