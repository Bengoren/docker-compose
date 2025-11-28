#!/bin/bash
set -e

echo "=== Food Trucks Setup Script ==="
echo ""

# Step 1: Build the image to generate static files
echo "Building Flask image (this generates static files)..."
docker build -t foodtrucks-builder --target builder .

# Step 2: Extract static files from builder
echo "Extracting static files..."
rm -rf static-dist
mkdir -p static-dist
docker create --name temp-extract foodtrucks-builder
docker cp temp-extract:/app/static/. static-dist/
docker cp temp-extract:/app/templates/index.html static-dist/
docker rm temp-extract

echo ""
echo "✓ Static files extracted to ./static-dist/"
echo ""
echo "Now starting all services..."
docker-compose up -d

echo ""
echo "✓ Setup complete!"
echo "Access the app at: http://localhost"