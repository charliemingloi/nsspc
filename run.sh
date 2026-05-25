#!/bin/bash
set -e

cd "$(dirname "$0")/backend"

if [ ! -f "../.env" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "⚠️  Warning: ANTHROPIC_API_KEY not set. Create a .env file or export the variable."
  echo "   Example: export ANTHROPIC_API_KEY=sk-ant-..."
fi

pip install -q -r requirements.txt

echo ""
echo "🌾 Starting AgroSmart AI Platform..."
echo "   → Open http://localhost:8000 in your browser"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
