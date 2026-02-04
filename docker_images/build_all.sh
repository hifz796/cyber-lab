#!/bin/bash

# CyberLab - Build All Docker Challenge Images

echo "======================================================"
echo "  🐳 Building All CyberLab Challenge Images"
echo "======================================================"
echo ""

cd "$(dirname "$0")"

# Array of challenges to build
declare -a challenges=(
    "01-sql-injection:SQL Injection Basics"
    "02-xss-attack:XSS Attack Vector"
    "03-command-injection:Command Injection"
    "04-directory-traversal:Directory Traversal"
    "09-cryptography:Cryptography Challenges"
)

# Build each challenge
for challenge in "${challenges[@]}"
do
    IFS=':' read -r -a parts <<< "$challenge"
    dockerfile="Dockerfile.${parts[0]}"
    name="${parts[1]}"
    tag="cyberLab/${parts[0]}:v1"
    
    echo "Building: $name"
    echo "Tag: $tag"
    echo "Dockerfile: $dockerfile"
    echo ""
    
    if [ -f "$dockerfile" ]; then
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
docker build -t "$tag" -f "$SCRIPT_DIR/$dockerfile" "$SCRIPT_DIR"
        
        if [ $? -eq 0 ]; then
            echo "✅ Built: $tag"
        else
            echo "❌ Failed: $tag"
        fi
    else
        echo "⚠️  Dockerfile not found: $dockerfile"
    fi
    
    echo "------------------------------------------------------"
    echo ""
done

echo "======================================================"
echo "  📊 Build Summary"
echo "======================================================"
docker images | grep cyberlab

echo ""
echo "======================================================"
echo "  🚀 Testing Instructions"
echo "======================================================"
echo "Test individual challenges:"
echo "  docker run -p 8001:80 cyberlab/01-sql-injection:v1"
echo "  docker run -p 8002:80 cyberlab/02-xss-attack:v1"
echo "  docker run -p 8003:80 cyberlab/03-command-injection:v1"
echo ""
echo "Then visit: http://localhost:800X"
echo "======================================================"