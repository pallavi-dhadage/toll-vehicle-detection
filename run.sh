#!/bin/bash
echo "🚗 Starting TollPlaza AI System..."

# Activate virtual environment
source venv/bin/activate

# Start backend
echo "Starting backend server..."
python app/main.py &

# Wait for backend
sleep 3

# Start frontend
echo "Starting frontend server..."
cd frontend
python3 -m http.server 3000 &
cd ..

echo ""
echo "✅ System Running!"
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend: http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

wait
