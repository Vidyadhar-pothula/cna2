#!/bin/bash
echo "--- Setting up Environment ---"
if [ -f .env ]; then
    export $(cat .env | xargs)
fi
pip3 install -r ml_prototype/requirements.txt

echo "--- Starting Application ---"
echo "Open your browser to: http://localhost:8000"
python3 app.py
