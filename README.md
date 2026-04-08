# AutoPM — Autonomous Code Review & Product Intelligence System

> Transforms real-time user complaints from Reddit into production-ready, AI-reviewed code.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) Google Gemini API Key (free)

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Copy env template and add your keys (optional — works without them in demo mode)
copy .env.example .env

# Start the backend server
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install

# Start the dev server (proxies API calls to localhost:8000)
npm run dev
```

### 3. Open the App

Visit **http://localhost:3000** in your browser.

## 🎮 How to Use

1. **Toggle Mode**: Switch between Demo (cached posts) and Live mode
2. **Fetch Posts**: Click the fetch button to load posts from Reddit
3. **Process**: Click "Process with AI" on any post
4. **Watch the Pipeline**: See the 5-stage AI pipeline run:
   - 🏷️ **Classify** — Bug / Feature Request / Performance + Priority
   - 📋 **Task** — Engineering task with acceptance criteria
   - 💻 **Code** — Generated implementation code
   - 🔍 **Review** — AI code review with score and feedback
   - 📦 **PR** — GitHub-style Pull Request summary

## 🔑 API Keys (Optional)

The system works **without any API keys** using intelligent mock responses and Reddit's public JSON endpoints. To enable real AI:

### Google Gemini API (Free)
Get your free API key from [Google AI Studio](https://aistudio.google.com/apikey)
```env
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.0-flash
```

## 📁 Project Structure

```
├── backend/
│   ├── main.py                 # FastAPI server
│   ├── pipeline/
│   │   ├── fetch_reddit.py     # Reddit public JSON fetching
│   │   ├── classify.py         # Issue classification
│   │   ├── task_generator.py   # Engineering task generation
│   │   ├── code_generator.py   # Code generation
│   │   ├── code_reviewer.py    # AI code review
│   │   └── pr_generator.py     # PR summary generation
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main application
│   │   ├── App.css             # Dark glassmorphism theme
│   │   └── components/
│   │       ├── Header.jsx      # App header with mode toggle
│   │       ├── PostCard.jsx    # Post display card
│   │       ├── PipelineView.jsx # Pipeline visualization
│   │       └── PROutput.jsx    # PR summary display
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 🛠️ API Endpoints

### Internal (FastAPI)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint returning basic app metadata |
| `/api/health` | GET | Health check + API key status |
| `/api/posts?mode=demo\|live` | GET | Fetch Reddit posts |
| `/api/process` | POST | Run full AI pipeline on a post |

### External 
| Service | Endpoint / SDK | Description |
|---------|----------|-------------|
| **Reddit** | `GET https://www.reddit.com/r/{subreddit}/new.json` | Fetches the latest public posts without requiring authentication |
| **Google Gemini** | `google-generativeai` SDK | Processes text to classify issues, generate tasks, create code, and write PRs |

## ⚡ Tech Stack

- **Backend**: Python, FastAPI, Requests, Google Gemini SDK
- **Frontend**: React 18, Vite
- **Styling**: Custom CSS with glassmorphism dark theme
- **Fonts**: Inter + JetBrains Mono
