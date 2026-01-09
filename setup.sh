#!/bin/bash
# Setup script for Variant Dashboard
# Run this after cloning the repository to set up hidden config files

echo "Setting up Variant Dashboard..."

# Rename config files to their proper hidden names
if [ -f "gitignore.txt" ]; then
    mv gitignore.txt .gitignore
    echo "✓ Created .gitignore"
fi

if [ -f "dockerignore.txt" ]; then
    mv dockerignore.txt .dockerignore
    echo "✓ Created .dockerignore"
fi

if [ -f "gcloudignore.txt" ]; then
    mv gcloudignore.txt .gcloudignore
    echo "✓ Created .gcloudignore"
fi

echo ""
echo "Setup complete! You can now:"
echo "  1. Run locally: streamlit run app/main.py"
echo "  2. Build Docker: docker build -t variant-dashboard ."
echo "  3. Deploy to Cloud Run: See DEPLOYMENT.md"
