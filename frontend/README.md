# DataHarbour Frontend

Modern React application for DataHarbour - A comprehensive data engineering platform.

## Tech Stack

- **React 18** - UI library
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **React Router** - Routing
- **Axios** - HTTP client
- **Chart.js** - Data visualization
- **CodeMirror** - Code editor
- **Lucide React** - Icons

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

The app will be available at http://localhost:3000

### Development

```bash
# Start dev server with HMR
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Project Structure

```
src/
├── components/
│   ├── layout/          # Layout components (Sidebar, Header)
│   ├── ui/              # Reusable UI components
│   └── features/        # Feature-specific components
├── pages/               # Page components
├── services/            # API and WebSocket services
├── store/               # Zustand state management
├── utils/               # Utility functions
├── App.jsx              # Root component
└── main.jsx             # Entry point
```

## Features

- ✅ Dashboard with stats and charts
- ✅ Jobs management (create, view, kill, restart)
- ✅ Notebooks editor with CodeMirror
- ✅ Clusters management
- ✅ Real-time monitoring
- ✅ WebSocket real-time updates
- ✅ Responsive design
- ✅ Modern UI with Tailwind CSS

## Environment Variables

See `.env.example` for required environment variables.

## Docker

### Development

```bash
docker build -t dataharbour-frontend:dev -f Dockerfile.dev .
docker run -p 3000:3000 dataharbour-frontend:dev
```

### Production

```bash
docker build -t dataharbour-frontend:latest .
docker run -p 80:80 dataharbour-frontend:latest
```

## Contributing

See [TRACK2_IMPLEMENTATION.md](../TRACK2_IMPLEMENTATION.md) for architecture details.

## License

[Your License]
