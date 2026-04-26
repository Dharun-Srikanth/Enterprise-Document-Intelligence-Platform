# Enterprise Document Intelligence Platform with Sustainability Analytics

A full-stack AI-powered platform that ingests documents and tear-down photos, extracts structured data, estimates costs and carbon footprint, and exposes dual query interfaces (Natural Language to SQL + RAG) for consultants to analyze cost-saving opportunities and sustainability trade-offs.

---

## Table of Contents

- [Enterprise Document Intelligence Platform with Sustainability Analytics](#enterprise-document-intelligence-platform-with-sustainability-analytics)
  - [Table of Contents](#table-of-contents)
  - [About the Project](#about-the-project)
  - [Key Features](#key-features)
  - [Architecture Overview](#architecture-overview)
  - [Tech Stack](#tech-stack)
  - [Project Structure](#project-structure)
  - [Setup \& Run](#setup--run)
    - [Prerequisites](#prerequisites)
    - [Option A: Docker Compose (Recommended)](#option-a-docker-compose-recommended)
    - [Option B: Run Locally Without Docker](#option-b-run-locally-without-docker)
      - [1. Install System Dependencies](#1-install-system-dependencies)
      - [2. Set Up the Database](#2-set-up-the-database)
      - [3. Configure Environment Variables](#3-configure-environment-variables)
      - [4. Start the Backend](#4-start-the-backend)
      - [5. Start the Frontend](#5-start-the-frontend)
  - [How to Use](#how-to-use)
    - [1. Upload Documents](#1-upload-documents)
    - [2. Browse Documents](#2-browse-documents)
    - [3. Ask SQL Questions (Structured Query)](#3-ask-sql-questions-structured-query)
    - [4. Ask Analytical Questions (RAG Query)](#4-ask-analytical-questions-rag-query)
    - [5. Dashboard](#5-dashboard)
  - [API Endpoints](#api-endpoints)
  - [System Design](#system-design)
    - [Layer 1: Document Ingestion \& OCR](#layer-1-document-ingestion--ocr)
    - [Layer 2: Extraction, Classification \& Storage](#layer-2-extraction-classification--storage)
    - [Layer 3: RAG + Agentic Query](#layer-3-rag--agentic-query)
    - [Layer 4: Natural Language → SQL](#layer-4-natural-language--sql)
  - [Database Schema](#database-schema)
  - [Design Decisions \& Trade-offs](#design-decisions--trade-offs)
  - [Future Improvements](#future-improvements)
  - [Test Data](#test-data)
  - [License](#license)

---

## About the Project

This platform is built for management consultants working on product tear-down analyses and sustainability assessments. It solves a common workflow problem: teams deal with a mix of **digital documents** (financial reports, meeting notes, project specs), **scanned documents** (signed memos, vendor matrices), and **tear-down photos** (product component images). Each type needs different processing, but consultants need to query across all of them seamlessly.

The platform handles:
- **Ingesting** all three document types with automatic type detection
- **Extracting** structured data — entities from text, component/material/cost classification from photos
- **Estimating** carbon footprint using benchmark reference data
- **Querying** via two interfaces:
  - **Structured (SQL):** Ask questions in plain English, get SQL-backed tabular results
  - **Analytical (RAG):** Ask complex questions, get AI-synthesized answers with source citations

---

## Key Features

- **Smart Document Ingestion** — Automatic detection of digital documents, scanned documents, and tear-down photos
- **OCR Pipeline** — OpenCV preprocessing (deskew, denoise, binarize) + Tesseract OCR for scanned documents
- **AI-Powered Extraction** — GPT-4o vision for component/material classification, spaCy + LLM for entity extraction
- **Sustainability Analytics** — Carbon footprint estimation (kg CO2e) with benchmark cross-referencing
- **Natural Language to SQL** — Ask questions in plain English, see generated SQL and tabular results
- **RAG with Multi-hop Retrieval** — Two-agent architecture (Retriever + Synthesizer) with source citations
- **Confidence Scoring** — Every classification includes a 0–1 confidence score; low confidence items are flagged
- **Interactive Dashboard** — Real-time stats, document browsing, and dual query interfaces

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                           │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌─────────┐ │
│  │Dashboard  │ │ Upload   │ │ Documents │ │SQL Query │ │RAG Query│ │
│  └─────┬────┘ └────┬─────┘ └─────┬─────┘ └────┬─────┘ └────┬────┘ │
└────────┼──────────┼────────────┼────────────┼────────────┼─────────┘
         │          │            │            │            │
         ▼          ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Backend API (FastAPI)                            │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────────┐  │
│  │ Layer 1          │  │ Layer 3          │  │ Layer 4            │  │
│  │ Ingestion + OCR  │  │ RAG + Agentic    │  │ NL → SQL Agent     │  │
│  │ - Type Detection │  │ - Retriever Agent│  │ - Query Generation │  │
│  │ - Preprocessing  │  │ - Synthesizer    │  │ - SQL Validation   │  │
│  │ - OCR Engine     │  │ - Source Citing  │  │ - Error Recovery   │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬───────────┘  │
│           ▼                    │                     │              │
│  ┌─────────────────┐           │                     │              │
│  │ Layer 2          │           │                     │              │
│  │ Extract/Classify │           │                     │              │
│  │ - Stream A: Docs │           │                     │              │
│  │   NER, Classify, │           │                     │              │
│  │   Relationships  │           │                     │              │
│  │ - Stream B: Photo│           │                     │              │
│  │   Component ID,  │           │                     │              │
│  │   Material, Cost,│           │                     │              │
│  │   Carbon Footprint           │                     │              │
│  └────────┬────────┘           │                     │              │
│           ▼                    ▼                     ▼              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Storage Layer                              │   │
│  │  ┌────────────────────┐      ┌────────────────────────────┐  │   │
│  │  │ PostgreSQL          │      │ ChromaDB (Vector Store)    │  │   │
│  │  │ - Documents         │      │ - Document Chunks          │  │   │
│  │  │ - Entities          │      │ - Embeddings               │  │   │
│  │  │ - Components        │      │ - Metadata Filters         │  │   │
│  │  │ - Relationships     │      │                            │  │   │
│  │  │ - Query Logs        │      │                            │  │   │
│  │  └────────────────────┘      └────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component           | Technology                              | Why                                                        |
| ------------------- | --------------------------------------- | ---------------------------------------------------------- |
| **Backend**         | FastAPI (Python 3.10+)                  | Async support, auto-generated OpenAPI docs, Python AI/ML ecosystem |
| **Frontend**        | Next.js 14 (React + TypeScript)         | Server-side rendering, API proxy rewrites, fast DX         |
| **Database**        | PostgreSQL 16                           | Robust relational DB, JSONB support, UUID primary keys     |
| **Vector Store**    | ChromaDB 0.5.5                          | Lightweight, Python-native, persistent local or server mode |
| **OCR**             | Tesseract 5 + pytesseract              | Free, reliable with OpenCV preprocessing                   |
| **Image Processing**| OpenCV (headless)                       | Skew correction, noise reduction, adaptive binarization    |
| **LLM**            | OpenAI GPT-4o + GPT-4o-mini             | Vision for photos, reasoning for agents, cost-efficient mini model |
| **Embeddings**      | OpenAI text-embedding-3-small           | Cost-effective, high quality for RAG retrieval              |
| **NER**             | spaCy (en_core_web_sm) + LLM           | Fast baseline NER with LLM refinement for domain entities  |
| **PDF Parsing**     | PyMuPDF (fitz)                          | Fast extraction of text + structure from PDFs               |
| **ORM**             | SQLAlchemy 2.0 (async)                  | Mature Python ORM with async session support                |
| **Containerization**| Docker + Docker Compose                 | Single-command deployment of all 4 services                 |

---

## Project Structure

```
AI_Engineer_Project/
├── .env.example                    # Template for environment variables
├── docker-compose.yml              # 4-service stack (postgres, chromadb, backend, frontend)
├── schema.sql                      # Database DDL (7 tables + indexes)
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                 # FastAPI entry point, CORS, route registration
│   │   ├── config.py               # Pydantic settings (loads from .env)
│   │   ├── api/
│   │   │   ├── upload.py           # POST /api/upload, GET /api/upload/status/{id}
│   │   │   ├── query.py            # POST /api/query/structured, POST /api/query/analytical
│   │   │   └── documents.py        # GET /api/documents, GET /api/documents/{id}, GET /api/components
│   │   ├── db/
│   │   │   ├── database.py         # Async SQLAlchemy engine + session
│   │   │   └── vector_store.py     # ChromaDB client (supports Docker or local persistent mode)
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── document.py         # Document table
│   │   │   ├── entity.py           # Extracted entities
│   │   │   ├── entity_relationship.py
│   │   │   ├── component.py        # Tear-down component classifications
│   │   │   ├── document_chunk.py   # Vector store chunk tracking
│   │   │   ├── query_log.py        # Query audit trail
│   │   │   └── benchmark.py        # Reference benchmark data
│   │   └── services/
│   │       ├── llm_client.py       # OpenAI wrapper with retry logic
│   │       ├── ingestion/          # Layer 1: Document Ingestion & OCR
│   │       │   ├── pipeline.py     # Main ingestion orchestrator
│   │       │   ├── detector.py     # MIME type + content-based type detection
│   │       │   ├── preprocessor.py # OpenCV image preprocessing
│   │       │   ├── ocr.py          # Tesseract OCR pipeline
│   │       │   └── pdf_parser.py   # PyMuPDF PDF text extraction
│   │       ├── extraction/         # Layer 2: Extraction & Classification
│   │       │   ├── pipeline.py     # Stream A (docs) + Stream B (photos) orchestrator
│   │       │   ├── entity_extractor.py    # spaCy + LLM entity extraction
│   │       │   ├── doc_classifier.py      # LLM document categorization
│   │       │   ├── relationship_mapper.py # Entity relationship extraction
│   │       │   ├── component_classifier.py # GPT-4o vision component/material ID
│   │       │   ├── sustainability.py      # Carbon footprint estimation
│   │       │   └── chunker.py             # Structure-aware document chunking
│   │       ├── rag/                # Layer 3: RAG + Agentic Query
│   │       │   ├── orchestrator.py        # RAG pipeline orchestrator
│   │       │   ├── retriever_agent.py     # Query decomposition + vector search
│   │       │   └── synthesizer_agent.py   # Cross-document reasoning + citations
│   │       └── sql_agent/          # Layer 4: Natural Language → SQL
│   │           ├── orchestrator.py        # NL→SQL pipeline orchestrator
│   │           ├── generator.py           # Schema-aware SQL generation via LLM
│   │           ├── validator.py           # SQL safety validation (blocks destructive ops)
│   │           └── executor.py            # Async SQL execution with error handling
│   ├── data/
│   │   └── benchmark.csv           # Component cost + carbon footprint reference data
│   └── tests/
│       ├── test_layer1.py          # Ingestion pipeline tests
│       ├── test_layer2.py          # Extraction pipeline tests
│       └── test_layer3.py          # RAG + SQL validator tests
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.js              # API proxy rewrite to backend
│   └── src/
│       ├── app/
│       │   ├── page.tsx            # Main page with 5-tab navigation
│       │   ├── layout.tsx          # Root layout
│       │   └── globals.css         # Styles (entity badges, stat cards, responsive)
│       ├── components/
│       │   ├── DashboardView.tsx    # Stats overview, breakdowns by type/category
│       │   ├── UploadView.tsx       # Drag-and-drop upload with status polling
│       │   ├── DocumentsView.tsx    # Document list + detail view (entities, text, components)
│       │   ├── StructuredQueryView.tsx  # NL→SQL interface with results table
│       │   └── AnalyticalQueryView.tsx  # RAG query with citations + confidence
│       └── lib/
│           └── api.ts              # Typed API client for all backend endpoints
│
└── test_data/                      # Sample test files
    ├── digital/                    # 5 text documents (financial, meeting notes, specs)
    ├── scanned/                    # 3 scanned images (memos, matrices, whiteboards)
    ├── teardown/                   # 5 tear-down component photos
    └── benchmark.csv               # Reference cost + emission data
```

---

## Setup & Run

### Prerequisites

- An **OpenAI API key** — Get one from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

---

### Option A: Docker Compose (Recommended)

This is the simplest way. Docker handles PostgreSQL, ChromaDB, backend, and frontend automatically.

**Requirements:** Docker and Docker Compose installed.

**Step 1: Clone the repository**
```bash
git clone <repo-url>
cd AI_Engineer_Project
```

**Step 2: Create the environment file**
```bash
cp .env.example .env
```

**Step 3: Add your OpenAI API key**

Open `.env` in any text editor and replace the placeholder:
```
OPENAI_API_KEY=sk-proj-your-actual-key-here
```
Leave all other values as-is — the defaults are configured for Docker.

**Step 4: Start everything**
```bash
docker-compose up --build
```

Wait until you see all services are healthy (typically 30–60 seconds).

**Step 5: Open the app**

| Service              | URL                              |
| -------------------- | -------------------------------- |
| **Frontend (UI)**    | http://localhost:3000             |
| **Backend API**      | http://localhost:8000             |
| **API Documentation**| http://localhost:8000/docs        |

**To stop:**
```bash
docker-compose down
```

---

### Option B: Run Locally Without Docker

Use this if you don't have Docker or want to run each service individually.

#### 1. Install System Dependencies

**PostgreSQL 16:**
- **Windows:** Download from [postgresql.org](https://www.postgresql.org/download/windows/) or install via PgAdmin4
- **macOS:** `brew install postgresql@16`
- **Linux:** `sudo apt install postgresql-16`

**Tesseract OCR 5:**
- **Windows:** Download installer from [github.com/UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
- **macOS:** `brew install tesseract`
- **Linux:** `sudo apt install tesseract-ocr`

**Python 3.10+** and **Node.js 18+** are also required.

#### 2. Set Up the Database

Open a PostgreSQL client (psql, PgAdmin, etc.) and run:

```sql
-- Create the user and database
CREATE USER docuser WITH PASSWORD 'docpass';
CREATE DATABASE docintell OWNER docuser;

-- Connect to the new database
\c docintell

-- Create the pgcrypto extension (needed for UUID generation)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Run the schema (copy-paste the contents of schema.sql)
-- Or from the terminal:
-- psql -U docuser -d docintell -f schema.sql

-- Grant permissions (run as superuser if schema was created by postgres)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO docuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO docuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO docuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO docuser;
```

#### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# App
DEBUG=false

# Database — use localhost instead of Docker hostname
DATABASE_URL=postgresql+asyncpg://docuser:docpass@localhost:5432/docintell
DATABASE_URL_SYNC=postgresql://docuser:docpass@localhost:5432/docintell

# ChromaDB — use "local" for file-based storage (no separate server needed)
CHROMA_HOST=local
CHROMA_PORT=8000

# OpenAI — REQUIRED
OPENAI_API_KEY=sk-proj-your-actual-key-here

# LLM Models
LLM_MODEL=gpt-4o
LLM_MODEL_MINI=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# File Storage — use a relative path for local development
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=50

# Processing Thresholds
OCR_CONFIDENCE_THRESHOLD=0.6
CLASSIFICATION_CONFIDENCE_THRESHOLD=0.6
```

> **Key differences from Docker:** `DATABASE_URL` uses `localhost` instead of `postgres`, and `CHROMA_HOST` is set to `local` which uses file-based ChromaDB (no separate ChromaDB server needed).

#### 4. Start the Backend

```bash
cd backend

# Create a virtual environment (recommended)
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Download the spaCy language model
python -m spacy download en_core_web_sm

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

Verify: Open http://localhost:8000/api/health — you should see `{"status": "ok"}`.

#### 5. Start the Frontend

Open a **new terminal**:

```bash
cd frontend

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

You should see:
```
▲ Next.js 14.2.15
- Local: http://localhost:3000
```

Open http://localhost:3000 in your browser.

---

## How to Use

### 1. Upload Documents

- Go to the **Upload** tab
- Drag and drop files or click to browse
- The platform accepts:
  - **Text files** (.txt) — processed as digital documents
  - **PDFs** (.pdf) — auto-detected as digital or scanned
  - **Images** (.png, .jpg) — auto-detected as scanned documents or tear-down photos
- Processing starts automatically; status updates in real-time
- Sample files are provided in the `test_data/` folder

### 2. Browse Documents

- Go to the **Documents** tab
- See all uploaded documents with their type, category, and processing status
- Click any document to view:
  - Extracted text (for documents)
  - Classified entities (people, organizations, dates, money)
  - Component details (for tear-down photos): material, cost estimates, carbon footprint

### 3. Ask SQL Questions (Structured Query)

- Go to the **SQL Query** tab
- Type a question in plain English, for example:
  - *"Show all documents with their categories"*
  - *"What is the total estimated cost for all components?"*
  - *"List components where carbon footprint exceeds 5 kg CO2e"*
- The system generates SQL, validates it (blocks any destructive operations), executes it, and shows results in a table
- The generated SQL is displayed so you can verify the logic

### 4. Ask Analytical Questions (RAG Query)

- Go to the **RAG Query** tab
- Ask complex questions that require reasoning across multiple documents:
  - *"What cost-saving initiatives are mentioned across all project documents?"*
  - *"Which components have the highest sustainability impact?"*
  - *"Summarize the key decisions from the sprint 8 meeting"*
- The system retrieves relevant document chunks, synthesizes an answer, and shows source citations with relevance scores

### 5. Dashboard

- The **Dashboard** tab shows an overview:
  - Total documents, entities, and components
  - Breakdown by document type and category
  - Component classification summary

---

## API Endpoints

| Method | Endpoint                 | Description                                         |
| ------ | ------------------------ | --------------------------------------------------- |
| `GET`  | `/api/health`            | Health check                                        |
| `POST` | `/api/upload`            | Upload one or more files (multipart/form-data)      |
| `GET`  | `/api/upload/status/{id}`| Get processing status for a document                |
| `GET`  | `/api/documents`         | List all documents with metadata                    |
| `GET`  | `/api/documents/{id}`    | Get document detail with entities, components, chunks |
| `GET`  | `/api/components`        | List all classified tear-down components             |
| `POST` | `/api/query/structured`  | Natural language → SQL query                        |
| `POST` | `/api/query/analytical`  | RAG-based analytical query                          |

Full interactive documentation is available at http://localhost:8000/docs when the backend is running.

---

## System Design

### Layer 1: Document Ingestion & OCR

**Auto-detection logic:**
```
File received → Check MIME type + extension
  ├─ PDF with extractable text     → "digital_doc"     → Extract text via PyMuPDF
  ├─ PDF without text / Image      → Analyze content:
  │    ├─ Has text/table layout    → "scanned_doc"     → Preprocess → OCR
  │    └─ Has object/component     → "component_photo"  → Route to vision pipeline
  └─ TXT / DOCX                   → "digital_doc"     → Extract text directly
```

**OCR preprocessing pipeline:** Grayscale → Noise reduction → Skew correction → Adaptive binarization → Tesseract OCR

### Layer 2: Extraction, Classification & Storage

**Stream A (Documents):**
- Entity extraction (spaCy NER + LLM refinement for domain-specific entities)
- Document classification (Financial Report, Meeting Notes, Project Update, Executive Summary)
- Entity relationship mapping

**Stream B (Tear-Down Photos):**
- Component classification via GPT-4o vision
- Material identification via GPT-4o vision
- Cost + carbon footprint estimation from benchmark data
- Confidence scoring with automatic flagging of low-confidence results

### Layer 3: RAG + Agentic Query

Two-agent architecture:
- **Retriever Agent** — Decomposes complex questions into sub-queries, performs multi-hop vector search, ranks and deduplicates results
- **Synthesizer Agent** — Reasons across retrieved chunks, generates grounded answers with source citations and confidence scores
- **Fault tolerance** — Handles "not found" gracefully, answers partial results with caveats, retries on LLM failures

### Layer 4: Natural Language → SQL

Pipeline: NL question → LLM generates SQL (with full schema context) → Validate (blocks DROP/DELETE/UPDATE/ALTER/INSERT) → Execute → Return results

On SQL errors, the error message is fed back to the LLM for self-correction (max 2 retries).

---

## Database Schema

7 tables with UUID primary keys, JSONB metadata, and strategic indexes:

| Table                  | Purpose                                                         |
| ---------------------- | --------------------------------------------------------------- |
| `documents`            | All ingested files — metadata, extracted text, processing status |
| `entities`             | Named entities extracted from documents (people, orgs, dates, money) |
| `entity_relationships` | Relationships between entities (person→project, org→budget)     |
| `components`           | Tear-down classifications — type, material, cost, carbon footprint |
| `benchmark_data`       | Reference data for cost ranges and emission factors              |
| `document_chunks`      | Vector store tracking — chunk text, metadata, ChromaDB vector IDs |
| `query_logs`           | Audit trail for all queries (SQL and RAG)                        |

The full DDL is in `schema.sql`.

---

## Design Decisions & Trade-offs

| Decision | Rationale |
|----------|-----------|
| **FastAPI over Express** | Python ecosystem is superior for AI/ML tasks (spaCy, OpenCV, PyMuPDF). Async handles concurrent uploads well. |
| **GPT-4o for vision** | Best available model for component/material classification from photos. Single provider simplifies API management. |
| **GPT-4o-mini for text tasks** | Cost-efficient for NER refinement, classification, and SQL generation where full GPT-4o isn't needed. |
| **ChromaDB over Pinecone/Weaviate** | Lightweight, no external service needed, supports both Docker and local file-based mode. |
| **Tesseract over cloud OCR** | Free, no extra API key needed, good enough with OpenCV preprocessing. |
| **Two-agent RAG** | Separating retrieval from synthesis allows independent optimization and swapping of either component. |
| **PostgreSQL for all structured data** | Single relational DB for documents, entities, AND components enables cross-domain SQL queries. |
| **Structure-aware chunking** | Chunking by sections/headings preserves context better than fixed-size chunking. |
| **Dual ChromaDB modes** | Docker mode uses ChromaDB server; local mode uses file-based persistent storage — no extra setup needed. |

---

## Future Improvements

- **Production OCR** — Replace Tesseract with Azure Document Intelligence or Google Document AI for better table extraction
- **Fine-tuned models** — Fine-tune a smaller model on component classification for faster, cheaper inference
- **Streaming responses** — WebSocket for real-time processing status and streaming RAG answers
- **Caching layer** — Redis cache for repeated SQL queries and common RAG questions
- **Authentication** — JWT-based auth with role-based access control
- **Batch processing** — Celery + Redis for production-grade async task queue
- **Evaluation framework** — Automated metrics for RAG quality (faithfulness, relevance) and SQL accuracy
- **Multi-tenant support** — Organization-scoped document isolation
- **Export functionality** — Export query results as CSV/Excel/PDF reports

---

## Test Data

The `test_data/` folder includes sample files for testing all platform features:

| Folder      | Files | Description                                              |
| ----------- | ----- | -------------------------------------------------------- |
| `digital/`  | 5     | Text documents — financial summary, meeting notes, project specs, strategy brief |
| `scanned/`  | 3     | Scanned images — signed memo, vendor matrix, whiteboard notes |
| `teardown/` | 5     | Tear-down photos — seat frame, slide rail, recliner, wire spring, seat track |
| Root        | 1     | `benchmark.csv` — reference data for cost and carbon estimation |

---

## License

This project is created as part of a technical evaluation. All rights reserved.
