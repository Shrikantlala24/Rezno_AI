┌────────────────────────────────────────┐       SSE / REST         ┌─────────────────────────────────────────┐
│           FRONTEND (SPA)               │  ◄────────────────────►  │            BACKEND (API)                │
│  • React 19 + TypeScript + Vite        │    Streamed Steps &      │  • FastAPI (Async Python 3.11)          │
│  • Tailwind CSS + shadcn/ui (Radix UI) │    Instant LLM Tokens    │  • LangChain / Gemini / Anthropic       │
│  • react-force-graph-2d (Native Canvas)│                          │  • sentence-transformers (MiniLM)       │
│  • Zustand (Client State)              │                          │  • Clean Modular Service Layer          │
└────────────────────────────────────────┘                          └─────────────────────────────────────────┘
        │ Hosted on Vercel / Cloudflare                                     │ Hosted on Railway / Render / Fly.io
        │ (Free, Global CDN, 0 Build Headaches)                             │ (Dedicated Python Container)