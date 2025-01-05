# CiteSmart - Academic Reference Finder

A modern web application that helps you find relevant quotes and generate Harvard-style citations from PDF documents. Built with React, Vite, and Flask.

## Features

- Upload PDF academic papers or references
- Search for relevant quotes based on your text
- Automatically generates Harvard-style citations with page numbers
- Modern, responsive web interface built with React and Tailwind CSS
- Flask backend for PDF processing

## Project Structure

```
/
├── api/              # Serverless backend functions
│   └── index.py      # Main API handler
├── frontend/         # React frontend
│   ├── src/          # React source code
│   ├── package.json  # Frontend dependencies
│   └── vite.config.js
├── vercel.json       # Vercel deployment configuration
└── requirements.txt  # Python dependencies
```

## Local Development

### Backend Setup

1. Navigate to the project directory:
```bash
cd "Reference Finder"
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Start the Flask server:
```bash
python api/index.py
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Deployment

This project is configured for deployment on Vercel:

1. Fork or clone this repository
2. Import the project in Vercel:
   - Go to [vercel.com](https://vercel.com)
   - Click "Add New Project"
   - Import your GitHub repository
   - Vercel will automatically detect the configuration
3. Your application will be deployed and available at your Vercel URL

## Technologies Used

- **Frontend:**
  - React
  - Vite
  - Tailwind CSS
  - Axios

- **Backend:**
  - Python
  - Flask
  - PyPDF2
  - NLTK

## License

MIT License - feel free to use this project for your own purposes.
