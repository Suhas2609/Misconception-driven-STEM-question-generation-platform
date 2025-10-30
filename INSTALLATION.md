# 🚀 Installation & Setup Guide

Complete guide for setting up the **Misconception-driven STEM Question Generation Platform** on your local machine.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker - Recommended)](#quick-start-docker)
3. [Manual Setup (Without Docker)](#manual-setup-without-docker)
4. [Environment Configuration](#environment-configuration)
5. [Running the Application](#running-the-application)
6. [Verification & Testing](#verification--testing)
7. [Troubleshooting](#troubleshooting)
8. [Project Structure](#project-structure)

---

## 📦 Prerequisites

### Required Software

| Software | Version | Download Link |
|----------|---------|---------------|
| **Git** | Latest | https://git-scm.com/downloads |
| **Docker Desktop** | Latest | https://www.docker.com/products/docker-desktop/ |
| **Node.js** | 18.x or higher | https://nodejs.org/ |
| **Python** | 3.11+ | https://www.python.org/downloads/ |

### Required API Keys

| Service | Purpose | Get Key From |
|---------|---------|--------------|
| **OpenAI API** | GPT-4o for question generation | https://platform.openai.com/api-keys |

### System Requirements

- **OS**: Windows 10/11, macOS, or Linux
- **RAM**: Minimum 8GB (16GB recommended)
- **Disk Space**: ~5GB free space
- **Internet**: Required for initial setup

---

## 🚀 Quick Start (Docker - Recommended)

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/Suhas2609/Misconception-driven-STEM-question-generation-platform.git

# Navigate to project directory
cd Misconception-driven-STEM-question-generation-platform
```

### Step 2: Create Environment File

Create a `.env` file in the `misconception_stem_rag` directory:

```bash
cd misconception_stem_rag
```

Create `.env` file with this content:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o

# MongoDB Configuration
MONGO_URI=mongodb://mongo:27017
MONGO_DB_NAME=adaptive_learning

# ChromaDB Configuration
CHROMA_HOST=chromadb
CHROMA_PORT=8001

# Redis Configuration
REDIS_URL=redis://redis:6379

# JWT Secret (change this to a random string)
SECRET_KEY=your_super_secret_key_change_this_in_production

# Application Settings
ENVIRONMENT=development
DEBUG=true
```

**⚠️ Important**: Replace `your_openai_api_key_here` with your actual OpenAI API key!

### Step 3: Start Docker Services

```bash
# Start all services (backend + databases)
docker-compose up -d

# Check if containers are running
docker-compose ps
```

You should see 4 containers running:
- `adaptive_api` (Backend API)
- `mongo` (MongoDB)
- `redis` (Redis)
- `chroma` (ChromaDB)

### Step 4: Setup Frontend

Open a **new terminal** and run:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Step 5: Access the Application

**Frontend**: http://localhost:5173  
**Backend API**: http://localhost:8000  
**API Docs**: http://localhost:8000/docs  

---

## 🔧 Manual Setup (Without Docker)

### Step 1: Clone Repository

```bash
git clone https://github.com/Suhas2609/Misconception-driven-STEM-question-generation-platform.git
cd Misconception-driven-STEM-question-generation-platform
```

### Step 2: Install MongoDB

**Windows**:
1. Download from https://www.mongodb.com/try/download/community
2. Install with default settings
3. MongoDB runs on `mongodb://localhost:27017`

**macOS** (using Homebrew):
```bash
brew tap mongodb/brew
brew install mongodb-community@6.0
brew services start mongodb-community@6.0
```

**Linux** (Ubuntu):
```bash
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
```

### Step 3: Install Redis

**Windows**:
1. Download from https://redis.io/download
2. Or use WSL: `wsl --install` then install Redis in WSL

**macOS**:
```bash
brew install redis
brew services start redis
```

**Linux**:
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

### Step 4: Install ChromaDB

```bash
pip install chromadb
```

Start ChromaDB server:
```bash
chroma run --host localhost --port 8001
```

### Step 5: Setup Backend

```bash
cd misconception_stem_rag

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download NLP models
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
python -m spacy download en_core_web_sm
python -m textblob.download_corpora
```

Create `.env` file in `misconception_stem_rag` directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=adaptive_learning
CHROMA_HOST=localhost
CHROMA_PORT=8001
REDIS_URL=redis://localhost:6379
SECRET_KEY=your_super_secret_key_change_this
ENVIRONMENT=development
DEBUG=true
```

Start backend:
```bash
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 6: Setup Frontend

Open a **new terminal**:

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

---

## ⚙️ Environment Configuration

### Backend Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o | `sk-proj-...` |
| `OPENAI_MODEL` | Model to use | `gpt-4o` |
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGO_DB_NAME` | Database name | `adaptive_learning` |
| `CHROMA_HOST` | ChromaDB host | `localhost` or `chromadb` (Docker) |
| `CHROMA_PORT` | ChromaDB port | `8001` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `SECRET_KEY` | JWT secret key | Random string (keep secret!) |
| `ENVIRONMENT` | Environment mode | `development` or `production` |
| `DEBUG` | Debug mode | `true` or `false` |

### Frontend Configuration

The frontend automatically connects to the backend at `http://localhost:8000`.

If you need to change the backend URL, edit `frontend/src/api/client.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000';  // Change this if needed
```

---

## ▶️ Running the Application

### Using Docker (Recommended)

```bash
# Start everything
cd misconception_stem_rag
docker-compose up -d

# In a new terminal, start frontend
cd frontend
npm run dev

# Stop everything
docker-compose down

# View logs
docker-compose logs -f api
```

### Manual Setup

**Terminal 1 - ChromaDB**:
```bash
chroma run --host localhost --port 8001
```

**Terminal 2 - Backend**:
```bash
cd misconception_stem_rag
source venv/bin/activate  # or venv\Scripts\activate on Windows
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 3 - Frontend**:
```bash
cd frontend
npm run dev
```

---

## ✅ Verification & Testing

### 1. Check Backend Health

Open http://localhost:8000/docs in your browser. You should see the FastAPI Swagger documentation.

### 2. Test API Connection

```bash
# Test health endpoint
curl http://localhost:8000/

# Should return: {"status": "healthy"}
```

### 3. Check Database Connections

```bash
# Check MongoDB
docker exec -it mongo mongosh
> show dbs
> exit

# Check Redis
docker exec -it redis redis-cli
> ping
> exit

# Check ChromaDB
curl http://localhost:8001/api/v1/heartbeat
```

### 4. Test Frontend

1. Open http://localhost:5173
2. You should see the landing page
3. Try registering a new account
4. Complete the onboarding assessment
5. Upload a PDF and generate questions

---

## 🐛 Troubleshooting

### Common Issues

#### 1. **Docker containers won't start**

```bash
# Check if Docker is running
docker --version

# Remove old containers and volumes
docker-compose down -v

# Rebuild and restart
docker-compose up -d --build
```

#### 2. **OpenAI API errors**

**Error**: `AuthenticationError: Invalid API key`

**Solution**: 
- Check your `.env` file has the correct OpenAI API key
- Ensure no extra spaces around the key
- Verify the key is valid at https://platform.openai.com/api-keys

#### 3. **MongoDB connection errors**

```bash
# Check if MongoDB is running
docker exec -it mongo mongosh

# Restart MongoDB
docker-compose restart mongo
```

#### 4. **ChromaDB connection errors**

```bash
# Check ChromaDB logs
docker logs chroma

# Restart ChromaDB
docker-compose restart chromadb
```

#### 5. **Frontend won't start**

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Try different port if 5173 is busy
npm run dev -- --port 3000
```

#### 6. **Port already in use**

**Error**: `Port 8000 is already allocated`

**Solution**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8000 | xargs kill -9
```

#### 7. **CORS errors in browser**

**Solution**: Make sure backend is running on port 8000 and frontend on port 5173. The backend is configured to allow these origins.

#### 8. **NLP models not found**

```bash
# Inside Docker container
docker exec -it adaptive_api bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
python -m spacy download en_core_web_sm
python -m textblob.download_corpora
```

### Getting Help

If you encounter issues:

1. **Check logs**: `docker-compose logs -f api`
2. **Check GitHub Issues**: https://github.com/Suhas2609/Misconception-driven-STEM-question-generation-platform/issues
3. **Check API docs**: http://localhost:8000/docs
4. **Verify environment variables**: `cat .env` (in misconception_stem_rag directory)

---

## 📁 Project Structure

```
Misconception-driven-STEM-question-generation-platform/
├── frontend/                          # React frontend
│   ├── src/
│   │   ├── api/                      # API client
│   │   ├── components/               # React components
│   │   ├── context/                  # React context
│   │   ├── pages/                    # Page components
│   │   └── main.jsx                  # Entry point
│   ├── package.json
│   └── vite.config.js
│
├── misconception_stem_rag/           # Backend
│   ├── backend/
│   │   └── app/
│   │       ├── routes/               # API endpoints
│   │       ├── services/             # Business logic
│   │       ├── models/               # Data models
│   │       └── db/                   # Database connections
│   ├── data/
│   │   ├── misconceptions/           # Misconception CSV files
│   │   └── pdfs/                     # Uploaded PDFs
│   ├── docker-compose.yml            # Docker services
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env                          # Environment variables (create this)
│
├── INSTALLATION.md                   # This file
├── README.md                         # Project overview
└── Documentation files (.md)
```

---

## 🎯 First Steps After Installation

### 1. **Create an Account**
- Go to http://localhost:5173
- Click "Get Started" or "Register"
- Fill in your details

### 2. **Complete Onboarding**
- Answer the 5 diagnostic questions
- This calibrates your cognitive profile

### 3. **Upload a PDF**
- Click "Upload PDF"
- Select a STEM textbook/notes (Physics, Chemistry, Biology, Math)
- Topics will be auto-extracted

### 4. **Select Topics**
- Choose topics you want to practice
- System generates personalized questions

### 5. **Take a Quiz**
- Answer questions
- Get personalized feedback
- Track your misconceptions
- See cognitive trait evolution

---

## 🔐 Security Notes

**For Development**:
- Default `.env` is fine for local testing
- MongoDB has no authentication (local only)

**For Production**:
- Change `SECRET_KEY` to a strong random string
- Add MongoDB authentication
- Use HTTPS
- Don't commit `.env` to Git
- Use environment variables for secrets
- Set `DEBUG=false`
- Set `ENVIRONMENT=production`

---

## 📊 Resource Usage

**Expected resource usage**:
- **RAM**: ~2-4GB (all services)
- **Disk**: ~2GB (Docker images + data)
- **CPU**: Moderate (spikes during question generation)

**Optimization tips**:
- Use Docker for simpler resource management
- ChromaDB data persists in Docker volumes
- MongoDB data persists in Docker volumes
- PDFs are stored locally in `misconception_stem_rag/data/pdfs/`

---

## 🚀 Quick Commands Reference

```bash
# Start everything (Docker)
cd misconception_stem_rag && docker-compose up -d
cd ../frontend && npm run dev

# Stop everything
docker-compose down
# Press Ctrl+C in frontend terminal

# View logs
docker-compose logs -f api

# Restart backend
docker-compose restart api

# Clear all data (WARNING: Deletes everything!)
docker-compose down -v

# Update code (after git pull)
docker-compose up -d --build
cd ../frontend && npm install
```

---

## ✅ Verification Checklist

Before sharing with others, verify:

- [ ] Docker Desktop is installed and running
- [ ] Git is installed
- [ ] Node.js is installed (check with `node --version`)
- [ ] OpenAI API key is valid and has credits
- [ ] `.env` file is created in `misconception_stem_rag/` directory
- [ ] All 4 Docker containers are running (`docker-compose ps`)
- [ ] Backend API docs are accessible at http://localhost:8000/docs
- [ ] Frontend is accessible at http://localhost:5173
- [ ] Can register a new user
- [ ] Can complete onboarding assessment
- [ ] Can upload a PDF
- [ ] Can generate and take a quiz

---

## 🎓 What's Next?

After successful installation:

1. **Read the documentation**:
   - `README.md` - Project overview
   - `TOPIC_LEVEL_FILTERING.md` - Filtering system
   - `ADAPTIVE_LEARNING_PHASES.md` - Adaptive features

2. **Explore the system**:
   - Try different STEM subjects
   - Track your progress over multiple quizzes
   - See how misconceptions are tracked

3. **Development**:
   - Backend: http://localhost:8000/docs (FastAPI docs)
   - Frontend: Edit files in `frontend/src/`
   - Hot reload is enabled for both

---

## 📧 Support

If you encounter any issues during installation:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs: `docker-compose logs -f api`
3. Check GitHub Issues
4. Ensure all prerequisites are met
5. Verify `.env` file is configured correctly

---

**Happy Learning! 🎉**

The system is designed to help students learn through personalized, adaptive questions that target their specific misconceptions and cognitive weaknesses.
