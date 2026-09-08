# JRE Frontend — Beta Testing Dashboard

**Version:** 1.0.0-beta | **Framework:** Next.js 16 + React 19 + Tailwind CSS 4

---

## Overview

A lightweight, professional web interface for the Jyotish Reasoning Engine (JRE) beta testing program. Allows non-technical beta testers (professional astrologers) to interact with the engine without using cURL or Postman.

### Features

- 🔮 **Custom Evaluation** — Enter any birth data and get instant yoga analysis
- 📋 **Fixture Evaluation** — Select from 50+ pre-validated historical charts
- 📄 **Report Viewer** — View formatted Markdown reports with legal disclaimer
- 📝 **Feedback Submission** — Structured taxonomy for scientific feedback
- 📚 **Case Studies** — Browse 20 modern personality demonstrations

---

## Quick Start

### Prerequisites

- Node.js 18+ (recommended: 20+)
- npm or yarn
- JRE API running (Docker or local)

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
# .env.local (already configured)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Build for Production

```bash
npm run build
npm start
```

---

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout with Header
│   ├── page.tsx                # Home page
│   ├── evaluate/
│   │   ├── page.tsx            # Custom birth data evaluation
│   │   └── fixture/
│   │       └── page.tsx        # Historical chart evaluation
│   ├── report/
│   │   └── [evaluationId]/
│   │       └── page.tsx        # Markdown report viewer
│   ├── feedback/
│   │   └── page.tsx            # Structured feedback submission
│   └── case-studies/
│       └── page.tsx            # 20 personality case studies
├── components/
│   ├── Header.tsx              # Navigation header
│   └── ApiKeyInput.tsx         # Reusable API key input
├── lib/
│   └── api.ts                  # Centralized API client
├── .env.local                  # Environment configuration
└── package.json                # Dependencies
```

---

## Connecting to Staging API

The frontend communicates with the JRE API via the `NEXT_PUBLIC_API_URL` environment variable.

### Local Development

```bash
# Terminal 1: Start the API
cd /path/to/JRE
source .venv/bin/activate
uvicorn src.jrs.api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start the frontend
cd frontend
npm run dev
```

### Docker Staging

```bash
# Start the API
docker-compose -f docker-compose.staging.yml up -d

# Start the frontend
cd frontend
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

---

## API Keys

Your beta API key is stored in browser localStorage. Enter it on any page:

| Key | Tester |
|-----|--------|
| `jre-beta-key-alpha` | Tester A |
| `jre-beta-key-beta` | Tester B |
| `jre-beta-key-gamma` | Tester C |

---

## Pages

### Home (`/`)
Welcome page with quick links to all features and engine overview.

### Evaluate Custom (`/evaluate`)
Form to enter birth data (date, time, latitude, longitude, timezone) and run evaluation.

### Evaluate Fixture (`/evaluate/fixture`)
Dropdown to select from 50+ historical chart fixtures and run evaluation.

### Report Viewer (`/report/[evaluationId]`)
View the formatted Markdown report for any evaluation. Includes legal disclaimer.

### Feedback (`/feedback`)
Submit structured feedback with boolean taxonomy flags and free text.

### Case Studies (`/case-studies`)
Grid of 20 modern personality case studies, filterable by domain.

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Next.js 16 | React framework with App Router |
| React 19 | UI library |
| TypeScript | Type safety |
| Tailwind CSS 4 | Utility-first styling |
| Axios | HTTP client |
| React Hook Form | Form management |
| Zod | Schema validation |
| React Markdown | Markdown rendering |

---

## Building & Deployment

### Development
```bash
npm run dev    # Starts on http://localhost:3000
```

### Production Build
```bash
npm run build  # Creates optimized build
npm start      # Starts production server
```

### Static Export (for deployment)
```bash
npm run build  # Outputs to .next/
```

---

*JRE v1.0.0-beta — Engine frozen. No reasoning logic changes during beta.*
