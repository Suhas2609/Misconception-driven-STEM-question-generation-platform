# 📧 Setup Instructions for Team

Hi! Here's how to get the **Adaptive Learning Platform** running on your machine.

---

## ⏱️ Time Required: ~5-10 minutes

## 📋 Before You Start

### Download & Install These (if not already installed):

1. **Docker Desktop** (Required)
   - Windows/Mac: https://www.docker.com/products/docker-desktop/
   - Install and make sure it's running (you'll see a whale icon in your taskbar)

2. **Node.js** (Required - version 18 or higher)
   - Download: https://nodejs.org/
   - Choose the LTS (Long Term Support) version

3. **Git** (Required)
   - Windows: https://git-scm.com/download/win
   - Mac: Already installed or install via Homebrew: `brew install git`

4. **OpenAI API Key** (Required)
   - Go to: https://platform.openai.com/api-keys
   - Sign up if you don't have an account
   - Click "Create new secret key"
   - Copy the key (starts with `sk-...`)
   - ⚠️ **Keep this key safe!** You'll need it in step 3

---

## 🚀 Setup Steps

### 1️⃣ Clone the Project

Open Terminal (Mac/Linux) or PowerShell (Windows) and run:

```bash
git clone https://github.com/Suhas2609/Misconception-driven-STEM-question-generation-platform.git
cd Misconception-driven-STEM-question-generation-platform
```

### 2️⃣ Setup Backend Environment

```bash
cd misconception_stem_rag
```

**Windows (PowerShell)**:
```powershell
Copy-Item .env.example .env
notepad .env
```

**Mac/Linux**:
```bash
cp .env.example .env
nano .env
```

**In the `.env` file**, find this line:
```
OPENAI_API_KEY=your_openai_api_key_here
```

Replace `your_openai_api_key_here` with your actual OpenAI API key from step 4 above.

Save and close the file.

### 3️⃣ Start the Backend

Still in the `misconception_stem_rag` directory, run:

```bash
docker-compose up -d
```

This will download and start all backend services (takes 2-3 minutes first time).

**Check if it worked**:
```bash
docker-compose ps
```

You should see 4 services running:
- ✅ adaptive_api
- ✅ mongo
- ✅ redis
- ✅ chroma

### 4️⃣ Start the Frontend

Open a **NEW terminal window** and run:

```bash
cd frontend
npm install
npm run dev
```

**Wait** until you see something like:
```
  ➜  Local:   http://localhost:5173/
```

---

## ✅ Access the Application

Open your browser and go to: **http://localhost:5173**

You should see the landing page! 🎉

---

## 🎯 First Time Use

1. **Register**: Create your account
2. **Onboarding**: Answer 5 quick questions (calibrates your profile)
3. **Upload PDF**: Upload any STEM textbook or notes (Physics, Chemistry, Biology, Math)
4. **Take Quiz**: Select topics and start!

---

## 🛑 Stopping the Application

When you're done:

1. **Frontend**: Press `Ctrl+C` in the terminal where `npm run dev` is running
2. **Backend**: Run in the `misconception_stem_rag` directory:
   ```bash
   docker-compose down
   ```

---

## 🔄 Restarting Later

**Backend**:
```bash
cd misconception_stem_rag
docker-compose up -d
```

**Frontend** (in a new terminal):
```bash
cd frontend
npm run dev
```

---

## ❗ Common Issues & Solutions

### Issue: "Docker is not running"
**Solution**: Open Docker Desktop application

### Issue: "Port 8000 is already in use"
**Solution**: 
```bash
cd misconception_stem_rag
docker-compose down
docker-compose up -d
```

### Issue: "OpenAI API error"
**Solution**: 
- Double-check your API key in the `.env` file
- Make sure there are no extra spaces
- Verify the key is valid at https://platform.openai.com/api-keys

### Issue: Frontend shows "Network Error"
**Solution**: 
- Make sure backend is running: `docker-compose ps` (should show 4 services)
- Restart backend: `docker-compose restart api`

### Issue: Can't access http://localhost:5173
**Solution**: 
- Make sure `npm run dev` is running
- Try: `npm run dev -- --port 3000` (uses port 3000 instead)

---

## 📚 More Help

If you need more details, check these files in the project:

- **[QUICKSTART.md](./QUICKSTART.md)** - Quick 5-minute guide
- **[INSTALLATION.md](./INSTALLATION.md)** - Complete installation guide with troubleshooting

Or reach out to me!

---

## ✅ Quick Verification

Before you start using it, verify:

- [ ] Docker Desktop is running
- [ ] 4 Docker containers are running (`docker-compose ps`)
- [ ] Frontend terminal shows "Local: http://localhost:5173/"
- [ ] Can open http://localhost:5173 in browser
- [ ] Can open http://localhost:8000/docs (backend API docs)

---

## 🎉 You're Ready!

The platform will:
- ✅ Generate personalized questions based on your uploaded PDFs
- ✅ Track your cognitive traits (analytical depth, precision, etc.)
- ✅ Identify and target your specific misconceptions
- ✅ Adapt difficulty based on your performance
- ✅ Show your progress over time

Enjoy! 🚀
