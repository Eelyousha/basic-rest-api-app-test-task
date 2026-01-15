#!/bin/bash

# Test script for API endpoints
# Make sure the application is running before executing this script

API_KEY="your-secret-key"
BASE_URL="http://localhost:8000"

echo "==================================="
echo "Testing Organization Directory API"
echo "==================================="
echo ""

echo "1. Testing root endpoint..."
curl -s "$BASE_URL/" | python3 -m json.tool
echo ""

echo "2. Testing buildings endpoint..."
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/buildings" | python3 -m json.tool | head -20
echo ""

echo "3. Testing activities endpoint (flat)..."
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/activities" | python3 -m json.tool | head -20
echo ""

echo "4. Testing activities endpoint (tree)..."
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/activities?include_tree=true" | python3 -m json.tool | head -30
echo ""

echo "5. Testing organizations endpoint..."
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/organizations" | python3 -m json.tool | head -20
echo ""

echo "6. Testing organization by ID..."
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/organizations/1" | python3 -m json.tool
echo ""

echo "7. Testing organizations filter by activity_id (should include children)..."
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/organizations?activity_id=1" | python3 -m json.tool | head -20
echo ""

echo "8. Testing organizations filter by name..."
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/organizations?name=LLC" | python3 -m json.tool | head -20
echo ""

echo "9. Testing geo radius search..."
curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/organizations?lat=55.7558&lon=37.6173&radius=1000" | python3 -m json.tool | head -20
echo ""

echo "10. Testing without API key (should fail)..."
curl -s "$BASE_URL/organizations" | python3 -m json.tool
echo ""

echo "==================================="
echo "Tests completed!"
echo "==================================="
