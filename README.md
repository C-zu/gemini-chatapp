# 🤖 Gemini Multi-Modal Chat Application

A sophisticated **multi-modal chat application** built with **Streamlit** and **FastAPI**, powered by **Google's Gemini AI model - gemini-2.5-flash**. This application supports intelligent conversations across **text**, **images**, and **CSV data analysis** — all in one seamless interface.

## ✨ Features

### 💬 Core Chat Mode
- Multi-turn conversational chat with persistent memory
- Real-time streaming responses for natural conversation flow
- Markdown rendering support for rich text formatting
- Session-based chat history management

### 🖼️ Image Chat Mode
- Upload and analyze images using Gemini's vision capabilities
- Ask natural language questions about image content
- Supports `.jpg`, `.jpeg`, `.png` formats
- Secure base64 encoding for backend transfer

### 📊 CSV Chat Mode
- Upload CSV files or import from URLs
- Intelligent data analysis with natural language queries
- Automatic data preview and summary statistics
- Interactive plotting and visualization support
- Context-aware data exploration powered by Gemini AI

## 🚀 Quick Start

### 📋 Prerequisites
- Python **3.9.8**
- A valid **Google Gemini API key** ([Get one here](https://makersuite.google.com/app/apikey))
- Supabase to store chat histories.

### ⚙️ Installation

#### 1️⃣ Clone the repository
```bash
git clone <your-repo-url>
cd Chatbot
```

#### 2️⃣ Create a virtual environment
```bash
python -m venv .venv

# Activate it
# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

#### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```
or
```bash
pip install fastapi langchain google-generativeai plotly langchain_google_genai streamlit dotenv supabase langchain_experimental uvicorn
```
#### 4️⃣ Set up environment variables
Create a `.env` file in the project root and add your Gemini API key:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
```

## ▶️ Running the Application

### 🎨 Frontend (Streamlit)
```bash
cd frontend
streamlit main.py
```

### ⚡ Backend (FastAPI)
```bash
cd backend
py main.py
```

Once both services are running:
- **Frontend**: Open your browser at [http://localhost:8501](http://localhost:8501)
- **Backend API**: Available at [http://localhost:8000](http://localhost:8000)
- **API Documentation**: Visit [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API docs

## 📁 Project Structure

```
Chatbot/
├── frontend/                    # Streamlit frontend application
│   ├── main.py                 # Main Streamlit app entry point
│   ├── core_chat.py            # Core text chat functionality
│   ├── image_chat.py           # Image analysis chat mode
│   ├── csv_chat.py             # CSV data analysis mode
│   ├── components/
│   │   └── sidebar.py          # Sidebar navigation component
│   ├── services/
│   │   └── api_client.py       # FastAPI backend communication
│   └── utils/
│       ├── session_manager.py  # Chat session handling
│       ├── database_setup.py   # Database initialization
│       └── helpers.py          # Utility functions
│   
│   
│
├── backend/                     # FastAPI backend application
│   ├── main.py                 # FastAPI app entry point
│   ├── api/
│   │   ├── ai.py               # AI chat endpoints
│   │   ├── chat.py             # Chat management endpoints
│   │   └── sessions.py         # Session management endpoints
│   ├── services/
│   │   ├── chat_service.py     # Chat business logic
│   │   ├── chat_repository.py  # Chat data persistence
│   │   └── session_service.py  # Session management logic
│   ├── models/
│   │   └── schemas.py          # Pydantic data schemas
│   └── utils/
│       └── supabase_client.py  # Database client configuration
│
├── data/                        # Data storage directory
│   └── chats/                  # Chat session data files
│
├── requirements.txt            # Python dependencies
├── chainlit.md                 # Chainlit welcome screen
└── README.md                   # This file
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/ai/chat` | POST | Stream text-based chat responses |
| `/api/v1/ai/chat/image` | POST | Stream image analysis responses |
| `/api/v1/ai/chat/csv` | POST | CSV data analysis with plotting support |
| `/api/v1/sessions/{session_id}/messages` | GET | Retrieve messages from a session |
| `/api/v1/sessions/{session_id}/messages` | POST | Add a new message to a session |
| `/health` | GET | Health check endpoint |

## 🏗️ Architecture

### Frontend (Streamlit)
- **UI Rendering**: Clean, responsive interface with mode switching
- **File Handling**: Upload and processing of images and CSV files
- **Session Management**: Persistent chat sessions with history
- **Real-time Communication**: Streaming responses from backend

### Backend (FastAPI)
- **API Gateway**: RESTful endpoints with automatic documentation
- **AI Integration**: Seamless integration with Google Gemini models
- **Data Processing**: CSV analysis with pandas and plotly visualization
- **CORS Support**: Cross-origin requests for frontend communication

### AI Service (Gemini)
- **Text Processing**: Natural language understanding and generation
- **Vision Analysis**: Image content analysis and description
- **Data Analysis**: Intelligent CSV data exploration and insights
- **Streaming Responses**: Real-time response generation

## 🛠️ Technology Stack

- **Frontend**: Streamlit, Python
- **Backend**: FastAPI, Uvicorn
- **AI/ML**: Google Gemini API, LangChain
- **Data Processing**: Pandas, Plotly
- **Database**: Supabase (optional)

## 🔧 Configuration

### Environment Variables
- `GOOGLE_API_KEY`: Your Google Gemini API key
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase API key

### Model Configuration
The application uses `gemini-2.5-flash` by default. You can modify the model in `backend/services/ai_service.py`:
```python
def __init__(self, model_name="gemini-2.5-flash", temperature=0.3):
```
