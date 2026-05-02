#!/bin/bash

# AWS Porter - All-in-one Initialization and Execution Script
set -e

# --- Configuration ---
VENV_DIR=".venv"
PYTHON_CMD="python3"

echo "=========================================="
echo "      AWS Porter: Account Cloner          "
echo "=========================================="

# 1. Check Dependencies
echo "[1/3] Checking dependencies..."
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "Error: python3 is not installed."
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed."
    exit 1
fi

# 2. Initialize/Update Environment
echo "[2/3] Initializing environment..."
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON_CMD -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install -q --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
fi

# 3. Interactive Execution
echo "[3/3] Ready to start porting."
echo ""

# Prompt for AWS details if not provided as arguments
if [ -z "$1" ] || [ -z "$2" ]; then
    read -p "Source AWS Profile: " SOURCE_PROFILE
    read -p "Target AWS Profile: " TARGET_PROFILE
    read -p "Source AWS Region [us-east-1]: " SOURCE_REGION
    SOURCE_REGION=${SOURCE_REGION:-us-east-1}
    read -p "Target AWS Region [$SOURCE_REGION]: " TARGET_REGION
    TARGET_REGION=${TARGET_REGION:-$SOURCE_REGION}
else
    SOURCE_PROFILE=$1
    TARGET_PROFILE=$2
    SOURCE_REGION=${3:-us-east-1}
    TARGET_REGION=${4:-$SOURCE_REGION}
fi

echo ""
echo "Running: python -m aws_porter.main port --source-profile $SOURCE_PROFILE --target-profile $TARGET_PROFILE --source-region $SOURCE_REGION --target-region $TARGET_REGION"
echo ""

# Run the tool
python -m aws_porter.main port \
    --source-profile "$SOURCE_PROFILE" \
    --target-profile "$TARGET_PROFILE" \
    --source-region "$SOURCE_REGION" \
    --target-region "$TARGET_REGION"

DEACTIVATE_VENV="deactivate"
$DEACTIVATE_VENV
