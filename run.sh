#!/bin/bash

# Set base project path
PROJECT_DIR="/home/aman_mi_938/Lily"

# Navigate to base path
cd "$PROJECT_DIR"

# Redirect all output to log file
#exec > lily_run.log 2>&1

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source myenv/bin/activate || echo "❌ Virtualenv activation failed"

# Run Lily main script
echo "🚀 Launching Lily..."
python3 /home/aman_mi_938/Lily/version_2/main.py
