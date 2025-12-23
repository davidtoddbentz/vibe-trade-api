#!/bin/bash
# Script to fetch strategy by thread ID from production API

THREAD_ID="${1:-1082d251-7973-43e5-b894-c4eab11b1533}"
API_URL="${API_URL:-https://vibe-trade-api-kff5sbwvca-uc.a.run.app}"

echo "🔍 Fetching strategy for thread ID: $THREAD_ID"
echo "📡 API URL: $API_URL"
echo ""

# Make the request (JWT auth is disabled for now)
echo "📤 Making request (no auth required)..."
echo ""

# Build headers
headers=(-H "Content-Type: application/json")
if [ -n "$JWT_TOKEN" ]; then
    headers+=(-H "Authorization: Bearer $JWT_TOKEN")
    echo "   Using JWT token (optional)"
fi

response=$(curl -s -w "\n%{http_code}" \
    -X GET \
    "${headers[@]}" \
    "${API_URL}/api/strategies/threads/${THREAD_ID}/strategy")

# Split response and status code
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

echo "📥 Response (HTTP $http_code):"
echo ""

if [ "$http_code" -eq 200 ]; then
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
else
    echo "$body"
fi

echo ""

