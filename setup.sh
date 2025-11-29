#!/bin/bash
set -e

echo "=== Food Trucks Setup Script ==="
echo ""

# Step 1: Build the image to generate static files
echo "Building Flask image (this generates static files)..."
docker build -t foodtrucks-builder --target builder --no-cache .

# Step 2: Extract static files from builder with correct structure
echo "Extracting static files..."
rm -rf static-dist
mkdir -p static-dist

docker create --name temp-extract foodtrucks-builder
docker cp temp-extract:/app/static static-dist/static
docker cp temp-extract:/app/templates/index.html static-dist/index.html
docker rm temp-extract

# Step 3: Fix permissions
echo "Setting correct permissions..."
chmod -R 755 static-dist/

# Step 4: Start services with docker-compose
echo ""
echo "Starting all services..."
docker-compose down
docker-compose up -d

echo ""
echo "✓ Setup complete!"
echo "Access the app at: http://localhost"