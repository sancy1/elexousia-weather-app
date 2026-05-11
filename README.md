# EL-Exousia Weather

An intelligent weather forecasting application powered by AI, featuring real-time weather data, conversational AI forecasts, and personalized user experiences.

![EL-Exousia Weather](https://img.shields.io/badge/Weather-AI%20Powered-blue)
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
   pip install -r requirements.txt
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
   - Set `VITE_API_URL` to your backend URL

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
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your_google_client_id
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

The frontend will be available at `http://localhost:8080`

#### Access the Application

Open your browser and navigate to `http://localhost:8080`

### Docker Deployment

```bash
docker-compose up -d
```

The application will be available at `http://localhost:8080`

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

### Backend
- **FastAPI** - Web framework
- **Python 3.10+** - Programming language
- **PostgreSQL** - Database
- **Psycopg2** - Database adapter
- **LangChain** - AI framework for LLM orchestration
- **LangGraph** - Agent workflow orchestration
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
│   └── requirements.txt    # Python dependencies
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

## License

This project is proprietary software. All rights reserved.

## Acknowledgments

- Weather data provided by [WeatherAPI.com](https://www.weatherapi.com/)
- AI capabilities powered by [LangChain](https://langchain.com/)
- UI components inspired by modern design patterns

---

**Built with ❤️ by Elexousia Engineering**