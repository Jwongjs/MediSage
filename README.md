# AI Medical Assistant Web App

An intelligent medical diagnosis platform powered by LangGraph workflows and local AI models, featuring real-time symptom analysis, image classification, and comprehensive healthcare recommendations.

## 🌟 Features

### **Multi-Modal Medical Analysis**
- **Textual Symptom Analysis**: Advanced LLM-powered diagnosis from symptom descriptions
- **Medical Image Classification**: Skin lesion analysis using EfficientNet
- **Follow-up Interactions**: Dynamic questioning system for comprehensive diagnosis
- **Overall Analysis**: Synthesized insights from all available data sources

### **AI-Powered Chatbot Workflow**
- **LangGraph Integration**: Sophisticated agent orchestration and workflow management
- **Local Model Support**: Privacy-focused local LLM execution (Llama 3.1, BioMistral)
- **Real-time Processing**: WebSocket-based live updates and streaming responses
- **Confidence Scoring**: Quantified diagnostic confidence with threshold-based routing

### **Smart Healthcare Recommendations**
- **Specialist Referrals**: Intelligent matching with appropriate medical specialists
- **Urgency Assessment**: Automated severity classification and emergency detection
- **Self-care Guidance**: Personalized health management recommendations
- **Comprehensive Reports**: Detailed medical analysis summaries

## 🚀 Quick Start
### Prerequisites
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Git** with Git LFS for version control and model downloads
- **4GB+ RAM** for local AI models
- **Hugging Face account** (optional but recommended for model downloads)

### 1. Clone & Setup
```bash
git clone https://github.com/Jwongjs/AI-Medical-Assistant-Web-App.git
cd AI-Medical-Assistant-Web-App
```

### 2. Backend Setup
```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt
```
### 3. Model Configuration

**Required AI Models:**
The application requires the following AI models to function properly:

1) **Main Language Model**: `Llama-3.1-8B-UltraMedical.Q8_0.gguf`
   - **Source**: Hugging Face - https://huggingface.co/mradermacher/Llama-3.1-8B-UltraMedical-GGUF
   - **How to Get**: Direct download from HF

2) **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`
   - **Note**: Downloaded automatically via Python when first used

3) **Image Classification Model**:
- skin_lesion_efficientnetb0.pth (should be included within the folder, else download model, phase2_best.pth within the google drive https://drive.google.com/file/d/15LBP6awUDjMOQFftsVC1GxA6kpi-4Yj0/view?usp=sharing)

**After Downloading:**
Place the following models within
```bash
backend/ai_models/Llama-3.1-8B-UltraMedical.Q8_0.gguf
```

### 4. Start both end servers

#### - Backend Setup
```bash
python main.py
```

#### - Frontend Setup
```bash
cd my-app

# Install Node dependencies
npm install

# Start development server
npm start
```

### - Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs


## 📂 Project Structure

```
AI-Medical-Assistant-Web-App/
├── 📁 backend/                    # Python FastAPI backend
│   ├── 📁 adapters/              # Model abstraction layer
│   │   ├── base.py               # Base model interface
│   │   ├── local_model_adapter.py # Local LLM integration
│   │   ├── hf_api_adapter.py     # Hugging Face API client
│   │   └── skinlesion_efficientNet_adapter.py # Image classifier
│   ├── 📁 api/                   # REST API endpoints
│   ├── 📁 graphs/                # LangGraph workflow definitions
│   ├── 📁 managers/              # State & model management
│   ├── 📁 nodes/                 # Workflow node implementations
│   ├── 📁 schemas/               # Pydantic data models
│   ├── 📁 ai_models/             # Local AI model files
│   ├── main.py                   # FastAPI application entry
│   └── requirements.txt          # Python dependencies
├── 📁 my-app/                    # React TypeScript frontend
│   ├── 📁 src/
│   │   ├── 📁 components/        # Reusable UI components
│   │   ├── 📁 pages/             # Main application pages
│   │   ├── 📁 hooks/             # Custom React hooks
│   │   ├── 📁 services/          # API integration layer
│   │   ├── 📁 workflow/          # Workflow routing logic
│   │   └── 📁 types/             # TypeScript definitions
│   ├── package.json              # Node.js dependencies
│   └── tsconfig.json             # TypeScript configuration
├── 📁 4_deployment/              # Docker & Kubernetes configs
├── start-local-test.bat          # Windows startup script
└── README.md                     # This file
```

## 🔄 Workflow Stages

The application follows a sophisticated multi-stage workflow:

1. **Textual Analysis** → Initial symptom processing
2. **Follow-up Questions** → Dynamic clarification (optional)
3. **Image Analysis** → Medical image classification (optional)
4. **Overall Analysis** → Comprehensive data synthesis
5. **Medical Report** → Final comprehensive summary

## 🛠️ Development

### Key Technologies
- **Backend**: FastAPI, LangGraph, LangChain, Pydantic, llama-cpp-python
- **Frontend**: React 19, TypeScript, Custom CSS
- **AI Models**: Llama 3.1, BioMistral, EfficientNet
- **Deployment**: Docker, Kubernetes (optional)

### Design Principles
1. **Lazy Loading**: Minimal LLM output optimization
2. **Singleton Pattern**: Efficient model sharing
3. **Privacy-First**: Local model execution
4. **Real-time Updates**: WebSocket streaming

### Adding New Models
1. Implement the `ModelInterface` in `backend/adapters/base.py`
2. Create adapter class inheriting from `ModelInterface`
3. Register in `backend/managers/model_manager.py`
4. Update workflow nodes as needed

## 🧪 Testing

### Backend Tests
```bash
cd backend
python quick_test.py        # Local model testing
python hf_api_test.py         # Hugging Face integration
```

### Frontend Tests
```bash
cd my-app
npm test                      # Jest test suite
npm run build                 # Production build test
```

## 🚀 Deployment

### Local Development
```bash
# Windows
./start-local-test.bat

# Linux/Mac
./start-local-test.sh
```

<!-- ### Docker Deployment
```bash
cd 4_deployment/docker
docker-compose up -d
```

### Kubernetes Deployment
```bash
cd 4_deployment/kubernetes
kubectl apply -f medical-ai-deployment.yaml
``` -->

## 📊 Performance & Resources

### System Requirements
- **RAM**: 8GB minimum (16GB recommended for larger models)
- **Storage**: 10GB+ for AI models
- **CPU**: Multi-core processor recommended
- **GPU**: Optional (CUDA support for faster inference)

### Model Performance
- **Llama 3.1-8B**: ~4GB VRAM, 2-5 tokens/sec
- **EfficientNet**: ~1GB VRAM, <1sec inference
- **Embedding Model**: ~500MB RAM, <100ms
---
