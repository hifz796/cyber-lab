#!/bin/bash

# CyberLab - Build All Docker Challenge Images

echo "======================================================"
echo "  🐳 Building All CyberLab Challenge Images (15 Total)"
echo "======================================================"
echo ""

cd "$(dirname "$0")"

# Array of all challenges to build
declare -a challenges=(
    "01-sql-injection:SQL Injection Basics"
    "02-xss-attack:XSS Attack Vector"
    "03-command-injection:Command Injection"
    "04-directory-traversal:Directory Traversal"
    "05-buffer-overflow:Buffer Overflow 101"
    "06-format-string:Format String Vulnerability"
    "07-network-recon:Network Reconnaissance"
    "08-packet-analysis:Packet Analysis"
    "09-cryptography:Cryptography Challenges"
    "11-privilege-escalation:Privilege Escalation"
    "12-password-cracking:Password Cracking"
    "13-reverse-engineering:Reverse Engineering Basics"
    "14-osint:OSINT Challenge"
    "15-forensics:Digital Forensics"
)

built_count=0
failed_count=0

# Build each challenge
for challenge in "${challenges[@]}"
do
    IFS=':' read -r -a parts <<< "$challenge"
    dockerfile="Dockerfile.${parts[0]}"
    name="${parts[1]}"
    tag="cyberlab/${parts[0]}:v1"
    
    echo "======================================================"
    echo "Building: $name"
    echo "Tag: $tag"
    echo "Dockerfile: $dockerfile"
    echo ""
    
    if [ -f "$dockerfile" ]; then
        if docker build -t "$tag" -f "$dockerfile" . > /dev/null 2>&1; then
            echo "✅ Built: $tag"
            ((built_count++))
        else
            echo "❌ Failed: $tag"
            ((failed_count++))
        fi
    else
        echo "⚠️  Dockerfile not found: $dockerfile"
        ((failed_count++))
    fi
    
    echo ""
done

echo "======================================================"
echo "  📊 Build Summary"
echo "======================================================"
echo "✅ Successfully built: $built_count"
echo "❌ Failed: $failed_count"
echo "📦 Total images: $((built_count + failed_count))"
echo ""
echo "======================================================"
echo "  🐳 Docker Images"
echo "======================================================"
docker images | grep cyberlab

echo ""
echo "======================================================"
echo "  🚀 Next Steps"
echo "======================================================"
echo "1. Update database with Docker images:"
echo "   python update_docker_images.py"
echo ""
echo "2. Restart application:"
echo "   python app.py"
echo ""
echo "3. Test challenges in browser:"
echo "   http://localhost:5000"
echo "======================================================"