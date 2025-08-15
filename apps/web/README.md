# Interview Coach - Frontend

A polished, modern React application for interview practice with real-time audio analysis.

## Features

- **Question Loading**: Random SWE interview questions with clean UI
- **Audio Recording**: Browser-based recording with MediaRecorder API and fallback file upload
- **Real-time Processing**: Background job monitoring with status updates
- **Analysis Reports**: Comprehensive scoring with WPM, coverage, filler words, and tips
- **PDF Export**: Download detailed reports as PDF
- **Error Handling**: User-friendly error messages and fallbacks
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **Styling**: Tailwind CSS v4
- **State Management**: React Query (TanStack Query)
- **API Client**: Axios
- **TypeScript**: Fully typed components and API calls

## Architecture

### Components

- `QuestionCard`: Loads and displays interview questions
- `RecorderCard`: Handles audio recording with MediaRecorder API
- `JobStatusCard`: Monitors background job processing
- `ReportCard`: Displays analysis results with metrics
- `Toast`: Error and success notifications

### Pages

- `/` - Main dashboard (replaces the old mock page)
- `/mock` - Redirects to dashboard

### API Integration

Uses the existing FastAPI backend endpoints:
- `GET /questions/{role}` - Load questions
- `POST /sessions` - Create session
- `POST /jobs/enqueue` - Upload audio and start processing
- `GET /jobs/{jobId}` - Poll job status
- `GET /report/{sessionId}` - Get analysis results
- `GET /report/{sessionId}/pdf` - Download PDF

## Getting Started

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Set up environment**:
   Create `.env.local` with:
   ```
   NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

4. **Build for production**:
   ```bash
   npm run build
   ```

## User Flow

1. **Load Question**: Click "Load Question" to get a random SWE interview question
2. **Start Session**: Click "Start Session" to begin recording
3. **Record Audio**: Use the recording controls or upload an audio file
4. **Monitor Progress**: Watch real-time job status updates
5. **View Results**: See comprehensive analysis with metrics and tips
6. **Download Report**: Get a detailed PDF report
7. **Start New Session**: Begin again with a fresh question

## Error Handling

- **Microphone Access**: Graceful fallback to file upload if permissions denied
- **Browser Support**: File upload fallback for browsers without MediaRecorder
- **Network Errors**: User-friendly error messages with retry options
- **Job Failures**: Clear error display with session restart option

## Accessibility

- Semantic HTML structure
- ARIA labels and descriptions
- Keyboard navigation support
- Screen reader friendly
- High contrast color scheme

## Performance

- Optimized bundle size (~133KB first load)
- Efficient React Query caching
- Minimal re-renders with proper state management
- Lazy loading of components
