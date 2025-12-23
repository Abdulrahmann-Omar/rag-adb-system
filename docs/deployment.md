# Deployment Guide

Instructions for deploying the RAG system to various platforms.

---

## Local Development

### Quick Start

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/rag-adb-system.git
cd rag-adb-system

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GITHUB_TOKEN

# Run application
streamlit run app.py
```

### Development Mode

For hot-reload during development:

```bash
streamlit run app.py --server.runOnSave true
```

Access at: `http://localhost:8501`

---

## HuggingFace Spaces

### Prerequisites

1. [HuggingFace account](https://huggingface.co/join)
2. [HuggingFace access token](https://huggingface.co/settings/tokens)
3. GitHub repository with the code

### Step 1: Create Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Fill in details:
   - **Space name**: `rag-adb-system`
   - **License**: MIT
   - **SDK**: Streamlit
   - **Hardware**: CPU Basic (free)
3. Click "Create Space"

### Step 2: Configure Secrets

1. Go to Space Settings → Secrets
2. Add secret:
   - **Name**: `GITHUB_TOKEN`
   - **Value**: Your GitHub Personal Access Token

### Step 3: Push Code

**Option A: Git Push**
```bash
# Add HuggingFace remote
git remote add space https://huggingface.co/spaces/YOUR_USERNAME/rag-adb-system

# Push to HuggingFace
git push space main
```

**Option B: GitHub Actions (Automatic)**

The repository includes `.github/workflows/sync-hf.yml` for automatic deployment.

1. Add secrets to GitHub repository:
   - `HF_TOKEN`: HuggingFace access token
   - `HF_SPACE`: `YOUR_USERNAME/rag-adb-system`

2. Push to main branch - deployment happens automatically

### Step 4: Verify Deployment

1. Visit `https://huggingface.co/spaces/YOUR_USERNAME/rag-adb-system`
2. Wait for build to complete (2-5 minutes)
3. Test the application

### Troubleshooting HuggingFace

| Issue | Solution |
|-------|----------|
| Build fails | Check `requirements.txt` for version conflicts |
| App crashes on start | Verify `GITHUB_TOKEN` secret is set |
| Slow startup | First load downloads embedding model (~90MB) |
| Memory errors | Use smaller embedding model or reduce chunk size |

---

## Streamlit Cloud

### Prerequisites

1. [Streamlit Cloud account](https://share.streamlit.io/)
2. GitHub repository (public or private)

### Step 1: Connect Repository

1. Go to [share.streamlit.io](https://share.streamlit.io/)
2. Click "New app"
3. Select your GitHub repository
4. Choose:
   - **Branch**: main
   - **Main file**: app.py

### Step 2: Configure Secrets

1. Click "Advanced settings"
2. Add secrets in TOML format:

```toml
GITHUB_TOKEN = "your_github_token_here"
MODEL_NAME = "gpt-4o-mini"
```

### Step 3: Deploy

1. Click "Deploy"
2. Wait for deployment (3-5 minutes)
3. Access at `https://YOUR_APP.streamlit.app`

---

## Docker Deployment

### Dockerfile

Create `Dockerfile` in repository root:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Build and Run

```bash
# Build image
docker build -t rag-adb-system .

# Run container
docker run -p 8501:8501 \
  -e GITHUB_TOKEN=your_token_here \
  -v $(pwd)/data:/app/data \
  rag-adb-system
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  rag-app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

---

## Production Considerations

### Environment Variables

Never commit secrets. Use environment variables:

```bash
# Required
GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# Optional overrides
MODEL_NAME=gpt-4o-mini
CHUNK_SIZE=1000
TOP_K=5
```

### Secrets Management

| Platform | Method |
|----------|--------|
| HuggingFace | Space Secrets |
| Streamlit Cloud | TOML Secrets |
| Docker | Environment files |
| Cloud Providers | Secret Manager (AWS/GCP/Azure) |

### Performance Tuning

1. **Embedding Model Caching**
   - First load downloads model (~90MB)
   - Subsequent loads use cached model

2. **Index Persistence**
   - Save FAISS index after adding documents
   - Load from disk on startup

3. **Memory Optimization**
   - Use `faiss-cpu` (not GPU version)
   - Limit concurrent users with Streamlit settings

### Monitoring

Add logging for production:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
```

### Health Checks

The app includes built-in status in sidebar:
- Document count
- System ready state
- Feedback statistics

For external monitoring, check `http://localhost:8501/healthz` (Streamlit built-in).

---

## Backup Strategy

### Data to Backup

```
data/
├── vector_store/     # FAISS index (regenerable from PDFs)
└── processed/        # Cached text (regenerable)

logs/
├── queries.jsonl     # Query history (important)
└── feedback.jsonl    # User feedback (important)
```

### Backup Commands

```bash
# Backup logs
cp -r logs/ backup/logs_$(date +%Y%m%d)/

# Backup vector store (optional - can regenerate)
cp -r data/vector_store/ backup/index_$(date +%Y%m%d)/
```

---

## Scaling Considerations

For high traffic deployments:

| Component | Scaling Strategy |
|-----------|-----------------|
| Streamlit | Multiple replicas behind load balancer |
| FAISS | Shared volume or distributed index |
| LLM API | Rate limiting, retry logic |
| Embeddings | Pre-compute, cache embeddings |

For enterprise scale, consider:
- Kubernetes deployment
- Redis for session state
- PostgreSQL for feedback storage
- Prometheus/Grafana for monitoring
