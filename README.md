# Elexousia Weather

---

<div align="center">

## 🛡️ SECURITY & REPOSITORY DISCLOSURE

![Security Notice](https://img.shields.io/badge/SECURITY-DISCLOSURE-blue?style=for-the-badge&logo=github)

</div>

> [!IMPORTANT]
> **🔒 PUBLIC REPOSITORY — NON-CONFIDENTIAL SAMPLE**
>
> This repository is publicly accessible, owned by the author, and provided as a **non-confidential sample for security auditing purposes.**
>
> **Security & Privacy Assurance:**
>
> - ✅ Does not intentionally contain private credentials or authentication secrets.
> - ✅ Does not intentionally expose confidential or sensitive information.
> - ✅ Does not provide access to live production systems.
>
> **⚙️ Environment Configuration**
>
> - Environment variables must be configured locally.
> - Use `.env.example` as the reference template for creating your local `.env` file.
> - **Never commit actual credentials, API keys, or private environment configurations.**

---

An intelligent weather forecasting application powered by AI, featuring real-time weather data, conversational AI forecasts, and personalized user experiences.

![Elexousia Weather](https://img.shields.io/badge/Weather-AI%20Powered-blue)
![React](https://img.shields.io/badge/Frontend-React-61DAFB)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791)

## 🌟 Features

- **Real-Time Weather Data**: Current weather conditions with temperature, humidity, wind, UV index, and more
- **7-Day Forecast**: Daily and hourly forecast views for any city worldwide
- **AI Weather Assistant**: Conversational AI powered by LangChain, LangGraph, and RAG for personalized weather insights
- **User Authentication**: OAuth integration with Google for secure user accounts
- **Saved Locations**: Save and manage your favorite weather locations
- **Search History**: Track your recent weather searches
- **Clothing Advice**: AI-powered recommendations based on weather conditions
- **City Comparison**: Compare weather between multiple cities
- **Notifications**: Automated weather alerts for extreme conditions (rain, heat, cold)
- **Responsive Design**: Beautiful, modern UI that works on all devices

## 🏗️ Architecture & Design

This project follows an industrial-grade design pattern with a clean separation of concerns.

For a deep dive into the logic, database schemas, agentic workflows, and implementation details, please refer to the [Technical Documentation](./docs/Elexousia_Weather_FastAPI_Development_Plan.pdf).

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Development](#development)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (v18 or higher) - [Download](https://nodejs.org/)
- **Python** (v3.10 or higher) - [Download](https://www.python.org/)
- **PostgreSQL** (v14 or higher) - [Download](https://www.postgresql.org/)
- **Git** - [Download](https://git-scm.com/)

Optional (for Docker deployment):

- **Docker** (v20 or higher) - [Download](https://www.docker.com/)
- **Docker Compose** - Included with Docker Desktop

## Installation

### Option 1: Local Development

#### Backend Setup

1. **Navigate to the backend directory:**

   ```bash
   cd backend
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**

   **Windows:**

   ```bash
   venv\Scripts\activate
   ```

   **Mac/Linux:**

   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies:**

   ```bash
   pip install -r requirements/base.txt
   ```

   For development extras (tests, linters):

   ```bash
   pip install -r requirements/dev.txt
   ```

5. **Set up the database:**
   - Create a PostgreSQL database named `elexousia_weather`
   - Run migrations:
     ```bash
     python -m app.infrastructure.database.migrate
     ```

6. **Configure environment variables:**
   - Copy `.env.example` to `.env`
   - Fill in the required values (see [Environment Variables](#environment-variables))

#### Frontend Setup

1. **Navigate to the frontend directory:**

   ```bash
   cd frontend
   ```

2. **Install dependencies:**

   ```bash
   npm install
   ```

3. **Configure environment variables:**
   - Copy `.env.example` to `.env`
   - In dev mode the API client defaults to `http://localhost:8000`; set `VITE_API_BASE_URL` only if your backend runs elsewhere

### Option 2: Docker Deployment

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd elexousia-weather
   ```

2. **Create environment files:**
   - Copy `.env.example` to `backend/.env`
   - Copy `.env.example` to `frontend/.env`
   - Fill in the required values

3. **Start the application:**
   ```bash
   docker-compose up -d
   ```

## Environment Variables

### Backend (.env)

```env
# Application
APP_NAME=Elexousia Weather API
APP_VERSION=1.0.0

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/elexousia_weather

# Weather API
WEATHER_API_KEY=your_weatherapi_key_here

# LLM Provider (ollama | groq | gemini)
LLM_PROVIDER=groq

# Ollama (local, free)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Groq (cloud, OpenAI-compatible)
GROQ_API_KEY=your_groq_api_key_here
GROQ_BASE_URL=https://api.groq.com
GROQ_MODEL=openai/gpt-oss-120b
GROQ_PRIMARY_MODEL=openai/gpt-oss-120b
GROQ_FALLBACK_MODELS=openai/gpt-oss-20b,qwen/qwen3.8-27b

# Gemini (alternative cloud provider)
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# OAuth (Google)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8080/auth/callback

# Session
SECRET_KEY=your_secret_key_here_32_chars_minimum
COOKIE_NAME=elexousia_session

# CORS
ALLOWED_ORIGINS=http://localhost:8080,http://localhost:5173
```

### Frontend (.env)

```env
# API base URL (optional in dev — defaults to http://localhost:8000)
VITE_API_BASE_URL=http://localhost:8000

# OAuth feature flags
VITE_GOOGLE_OAUTH_ENABLED=true
VITE_GITHUB_OAUTH_ENABLED=true

# Feature flags
VITE_ENABLE_IDE_MODE=false
VITE_ENABLE_AGENT_MODE=false
```

## Running the Application

### Local Development

#### Start the Backend

**From the backend directory:**

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the provided script:

```bash
# Windows
.\start.ps1

# Mac/Linux
./start.sh
```

The backend will be available at `http://localhost:8000`

#### Start the Frontend

**From the frontend directory:**

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

#### Access the Application

Open your browser and navigate to `http://localhost:3000`

### Docker Deployment

```bash
docker-compose up -d
```

The application will be available at `http://localhost:3000`

## API Documentation

Once the backend is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Weather

- `GET /api/weather/current` - Get current weather for a city
- `GET /api/weather/forecast` - Get weather forecast
- `GET /api/weather/hourly` - Get hourly forecast
- `GET /api/weather/detail` - Get detailed weather information

#### Authentication

- `GET /api/auth/google` - Initiate Google OAuth
- `GET /api/auth/callback` - OAuth callback
- `GET /api/auth/me` - Get current user

#### AI Chat

- `POST /api/chat` - Send message to AI assistant

#### User Features

- `GET /api/saved-locations` - Get saved locations
- `POST /api/saved-locations` - Save a location
- `DELETE /api/saved-locations/{id}` - Delete a location
- `GET /api/search-history` - Get search history
- `POST /api/search-history` - Add to search history
- `GET /api/notifications` - Get notifications
- `PATCH /api/notifications/{id}/read` - Mark notification as read

## Tech Stack

### Frontend

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Lucide React** - Icons
- **TanStack Query** - Data fetching
- **React Router** - Routing
- **ReactMarkdown** - Markdown rendering for AI chat responses

### Backend

- **FastAPI** - Web framework
- **Python 3.10+** - Programming language
- **PostgreSQL** - Database
- **Psycopg2** - Database adapter
- **LangChain** - AI framework for LLM orchestration
- **LangGraph** - Agent workflow orchestration
- **Groq / Ollama / Gemini** - Pluggable LLM providers (switch via `LLM_PROVIDER`)
- **RAG** - Retrieval-Augmented Generation for context-aware responses
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

### Infrastructure

- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Reverse proxy

## Project Structure

```
elexousia-weather/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── agent/          # AI agent logic
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── infrastructure/ # Database & external services
│   │   └── main.py         # Application entry point
│   ├── migrations/         # Database migrations
│   ├── requirements/       # Python dependencies (base/dev/prod)
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom hooks
│   │   ├── lib/            # API client & utilities
│   │   └── routes/         # Page routes
│   └── package.json        # Node dependencies
├── docs/                   # Documentation
├── nginx/                  # Nginx configuration
├── docker-compose.yml      # Development Docker setup
├── docker-compose.prod.yml # Production Docker setup
└── README.md              # This file
```

## Development

### Backend Development

```bash
cd backend
python -m uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Style

- **Backend**: Follow PEP 8 guidelines
- **Frontend**: Use ESLint and Prettier for consistent formatting

## Deployment

### Production Deployment with Render

Render provides a simple way to deploy the backend from GitHub with managed infrastructure.

#### Backend Deployment

1. **Prepare your repository:**
   - Ensure `backend/Dockerfile` is present and properly configured
   - Ensure `backend/.dockerignore` is present to exclude unnecessary files
   - Push your code to GitHub

2. **Create a Render web service:**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - **Name**: `elexousia-weather-backend` (or your preferred name)
     - **Region**: Choose a region close to your users
     - **Branch**: `main` (or your production branch)
     - **Runtime**: Docker
     - **Docker Context**: `./backend`
     - **Dockerfile Path**: `Dockerfile`

3. **Configure environment variables:**
   In the "Advanced" section, add the following environment variables:

   ```env
   DATABASE_URL=postgresql://user:password@your-db-host:5432/elexousia_weather
   WEATHER_API_KEY=your_weatherapi_key_here
   LLM_PROVIDER=groq
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_BASE_URL=https://api.groq.com
   GROQ_MODEL=openai/gpt-oss-120b
   GROQ_PRIMARY_MODEL=openai/gpt-oss-120b
   GROQ_FALLBACK_MODELS=openai/gpt-oss-20b,qwen/qwen3.8-27b
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   GOOGLE_REDIRECT_URI=https://your-app.onrender.com/auth/callback
   SECRET_KEY=your_secret_key_here_32_chars_minimum
   COOKIE_NAME=elexousia_session
   ALLOWED_ORIGINS=https://your-app.onrender.com
   ```

4. **Configure database:**
   - Create a PostgreSQL database in Render (Database → New → PostgreSQL)
   - Copy the internal database URL from the Render dashboard
   - Update `DATABASE_URL` environment variable with the Render database URL

5. **Deploy:**
   - Click "Create Web Service"
   - Render will build and deploy your backend automatically
   - The backend will be available at `https://your-app.onrender.com`
   - Render provides automatic SSL certificates

#### Frontend Deployment

Deploy the frontend to Vercel, Netlify, or Render Static Sites:

**Option 1: Vercel**

1. Connect your repository to Vercel
2. Configure build settings:
   - Framework: Vite
   - Build command: `npm run build`
   - Output directory: `dist`
3. Add environment variables:
   - `VITE_API_URL`: Your Render backend URL
   - `VITE_GOOGLE_CLIENT_ID`: Your Google client ID
4. Deploy

**Option 2: Netlify**

1. Connect your repository to Netlify
2. Configure build settings:
   - Build command: `npm run build`
   - Publish directory: `dist`
3. Add environment variables in site settings
4. Deploy

**Option 3: Render Static Sites**

1. Create a new "Static Site" in Render
2. Connect your repository
3. Configure:
   - Build command: `cd frontend && npm install && npm run build`
   - Publish directory: `frontend/dist`
4. Add environment variables
5. Deploy

### Production Deployment with Docker

1. **Update environment files:**
   - Set production values in `backend/.env`
   - Set production values in `frontend/.env`

2. **Build and start:**

   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Configure Nginx:**
   - Update `nginx/nginx.conf` with your domain
   - Set up SSL certificates (Let's Encrypt recommended)

### Manual Deployment

#### Backend Deployment

1. **Set up PostgreSQL database**
2. **Configure environment variables**
3. **Run migrations**
4. **Start with Uvicorn:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

#### Frontend Deployment

1. **Build the application:**

   ```bash
   npm run build
   ```

2. **Deploy the `dist/` folder** to your web server or CDN

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

### Common Issues

**Backend won't start:**

- Ensure PostgreSQL is running
- Check database connection string in `.env`
- Verify all environment variables are set

**Frontend won't start:**

- Ensure VITE_API_URL is correct
- Check that backend is running
- Verify Node.js version is 18+

### Getting Help

- Check the [Technical Documentation](./docs/Elexousia_Weather_FastAPI_Development_Plan.pdf) for detailed implementation information
- Review API documentation at `/docs` endpoint
- Check logs in the backend console

---

<div align="center">

# 🛡️ SECURITY AUDIT SCOPE

![Audit Scope](https://img.shields.io/badge/SECURITY-AUDIT%20SCOPE-blue?style=for-the-badge&logo=github)
![Assessment](https://img.shields.io/badge/ASSESSMENT-AUTHORIZED-success?style=for-the-badge)
![Application](https://img.shields.io/badge/PROJECT-TECHFUND%20AI%20SECURITY-informational?style=for-the-badge)

**Defined Assessment Boundaries, Covered Components & Reporting Standards**

</div>

## 📋 Audit Overview

This repository is a **public, non-confidential sample application** owned by the repository owner. It is being made available for security assessment as part of a **TECHFUND AI Security Engineer application**.

The assessment is intended to evaluate the application's security posture across its backend, frontend, infrastructure configuration, authentication mechanisms, database interactions, and AI-powered components.

## 🎯 1. In-Scope Components

The following application components, source code, and configurations are included in the security audit:

| Area                            | Audit Coverage                                                       |
| ------------------------------- | -------------------------------------------------------------------- |
| 🐍 **Backend**                  | FastAPI backend source code                                          |
| 🔌 **API Security**             | API routes, request validation, and error handling                   |
| 🔐 **Authentication**           | Authentication, Google OAuth integration, and session handling       |
| 🗄️ **Database Security**        | PostgreSQL access, migrations, and data-access patterns              |
| ⚙️ **Environment Security**     | Environment configuration and secrets-management practices           |
| 🌦️ **External API Integration** | Third-party WeatherAPI integration                                   |
| 🤖 **AI/LLM Security**          | LLM, LangChain, LangGraph, and RAG-related code                      |
| 💬 **AI Processing**            | AI chat endpoint, agent workflow, retrieval pipeline, and tool usage |
| ⚛️ **Frontend**                 | React frontend source code and API client                            |
| 🐳 **Infrastructure**           | Docker, Docker Compose, and Nginx configuration                      |
| 📦 **Dependencies**             | Dependency and configuration security                                |

## 🚫 2. Out-of-Scope Components

The following systems, resources, and activities are explicitly excluded from this assessment:

- **Live Production Infrastructure:** No testing against live production environments.
- **External Third-Party Services:** No direct security testing of third-party services beyond the code and configurations contained in this repository.
- **Private or Sensitive Information:** No access to private credentials, confidential information, or customer data.
- **Live Penetration Testing:** No penetration testing against live systems.
- **Unauthorized Systems:** No testing of systems for which the auditor does not have explicit permission.

> [!WARNING]
> **Authorization Boundary:** The audit is limited to the repository and its included code and configurations. Any testing beyond these boundaries requires explicit authorization from the relevant system owner.

## 📝 3. Findings Validation & Reporting

All identified findings will undergo **manual review and validation** before inclusion in the final security report.

Each validated finding will document:

- 🔍 **Issue Description:** A clear explanation of the identified vulnerability or security weakness.
- 🧪 **Reproduction Steps:** Practical steps demonstrating how the issue can be reproduced.
- 💥 **Impact Assessment:** Potential consequences and associated security risks.
- 🚨 **Severity Classification:** An appropriate severity rating based on the assessed risk.
- 🛠️ **Recommended Remediation:** Practical recommendations for resolving or mitigating the issue.

If no security issues are identified, the final report will document:

- The assessment scope.
- Security checks and review procedures performed.
- Assessment limitations and any areas that could not be verified.

---

<div align="center">

**🔒 RESPONSIBLE SECURITY ASSESSMENT**

_All security testing and reporting must remain within the explicitly defined authorization boundaries._

</div>

---

## License

This project is proprietary software. All rights reserved.

See the [LICENSE](./LICENSE) file for details.

## Acknowledgments

- Weather data provided by [WeatherAPI.com](https://www.weatherapi.com/)
- AI capabilities powered by [LangChain](https://langchain.com/)
- UI components inspired by modern design patterns

- Live Demo: https://elexousia-weatherforecast-lovat.vercel.app
- Email: alexander.s.cyril@gmail.com

---

##

- SCREENSHOTS
  <img width="1917" height="872" alt="Elexousia" src="https://github.com/user-attachments/assets/baa2c48d-5301-49df-9af4-e3e3ea0b3ef5" />
  |->
  <img width="1905" height="867" alt="1" src="https://github.com/user-attachments/assets/a9b5fbed-0864-4714-b94d-34654cf53c84" />
  |->
  <img width="1431" height="555" alt="2" src="https://github.com/user-attachments/assets/660c7cbd-72fa-433c-b753-9f2a6046baab" />
  |->
  <img width="1896" height="863" alt="3" src="https://github.com/user-attachments/assets/9fa44367-e72b-4845-842f-5f87fbb1e25b" />
  |->
  <img width="1455" height="636" alt="4" src="https://github.com/user-attachments/assets/43a93caf-798a-4afd-88a6-c8c4e4bbec9f" />
  |->
  <img width="1463" height="685" alt="5" src="https://github.com/user-attachments/assets/fd7aecf2-3324-40b0-88cb-50d0b19d3ddd" />
  |->
  <img width="1456" height="617" alt="6" src="https://github.com/user-attachments/assets/3a7ae8be-54f8-4a7e-a4ea-64384d56d636" />
  |->
  <img width="1473" height="688" alt="7" src="https://github.com/user-attachments/assets/25f19648-8fc4-48d1-8f72-8e44a1c32afd" />
  |->
  <img width="1462" height="622" alt="8" src="https://github.com/user-attachments/assets/d6480e58-0daf-456c-bc7b-0b2cc9c2f4d0" />
  |->
  <img width="1452" height="683" alt="9" src="https://github.com/user-attachments/assets/3c351a38-6188-4e88-a76f-85015b460fd2" />

##

**Built by Alexander S. Cyril**
