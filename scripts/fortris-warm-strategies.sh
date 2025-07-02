#!/bin/bash
# Fortris Security-focused cache warming strategies

CACHE_DIR="$HOME/.claude/cache"
SCRIPT_DIR="$(dirname "$0")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔒 Fortris Security-Focused Cache Warming Strategies"
echo "=================================================="

# Strategy 1: Warm high-risk file types first
warm_high_risk() {
    echo -e "\n${BLUE}Strategy 1: High-Risk Files${NC}"
    echo "Caching files most likely to contain vulnerabilities..."
    
    # Authentication and config files
    fortris warm \
        "**/config*.py" "**/config*.js" "**/config*.yml" \
        "**/settings*.py" "**/settings*.js" \
        "**/.env*" "**/secrets*" "**/credentials*"
    
    # Database and SQL files
    fortris warm \
        "**/models*.py" "**/database*.py" "**/db*.py" \
        "**/*.sql" "**/queries*.py" "**/queries*.js"
    
    # API and network code
    fortris warm \
        "**/api*.py" "**/api*.js" "**/routes*.py" "**/routes*.js" \
        "**/views*.py" "**/controllers*.py" "**/handlers*.py"
    
    # Security-related files
    fortris warm \
        "**/auth*.py" "**/auth*.js" "**/security*.py" "**/security*.js" \
        "**/crypto*.py" "**/crypto*.js" "**/hash*.py" "**/hash*.js"
}

# Strategy 2: Warm by technology stack
warm_by_stack() {
    echo -e "\n${BLUE}Strategy 2: Technology Stack${NC}"
    echo "Select your technology stack:"
    echo "1) Python (Django/Flask/FastAPI)"
    echo "2) JavaScript (Node.js/React/Vue)"
    echo "3) Java (Spring/Struts)"
    echo "4) PHP (Laravel/Symfony)"
    echo "5) Ruby (Rails)"
    echo "6) Go"
    echo "7) All of the above"
    
    read -p "Enter choice (1-7): " choice
    
    case $choice in
        1)
            echo "Warming Python stack with Fortris..."
            fortris warm "**/*.py" "**/requirements*.txt" "**/Pipfile*" "**/*.yml"
            ;;
        2)
            echo "Warming JavaScript stack with Fortris..."
            fortris warm "**/*.js" "**/*.ts" "**/*.jsx" "**/*.tsx" "**/package*.json"
            ;;
        3)
            echo "Warming Java stack with Fortris..."
            fortris warm "**/*.java" "**/pom.xml" "**/build.gradle" "**/*.properties"
            ;;
        4)
            echo "Warming PHP stack with Fortris..."
            fortris warm "**/*.php" "**/composer.json" "**/.htaccess"
            ;;
        5)
            echo "Warming Ruby stack with Fortris..."
            fortris warm "**/*.rb" "**/Gemfile*" "**/*.erb"
            ;;
        6)
            echo "Warming Go stack with Fortris..."
            fortris warm "**/*.go" "**/go.mod" "**/go.sum"
            ;;
        7)
            echo "Warming all stacks with Fortris..."
            fortris warm "**/*.py" "**/*.js" "**/*.java" "**/*.php" "**/*.rb" "**/*.go"
            ;;
    esac
}

# Strategy 3: Warm by project structure
warm_by_structure() {
    echo -e "\n${BLUE}Strategy 3: Project Structure${NC}"
    echo "Analyzing project structure..."
    
    # Check for common project types
    if [ -f "package.json" ]; then
        echo "Detected Node.js project - warming with Fortris"
        fortris warm "src/**/*" "lib/**/*" "api/**/*" "config/**/*"
    elif [ -f "requirements.txt" ] || [ -f "setup.py" ]; then
        echo "Detected Python project - warming with Fortris"
        fortris warm "**/*.py" "tests/**/*" "config/**/*"
    elif [ -f "pom.xml" ] || [ -f "build.gradle" ]; then
        echo "Detected Java project - warming with Fortris"
        fortris warm "src/**/*.java" "src/**/*.xml" "src/**/*.properties"
    elif [ -f "composer.json" ]; then
        echo "Detected PHP project - warming with Fortris"
        fortris warm "src/**/*.php" "app/**/*.php" "config/**/*.php"
    else
        echo "Using generic structure with Fortris"
        fortris warm "src/**/*" "lib/**/*" "app/**/*" "config/**/*"
    fi
}

# Strategy 4: Warm recently modified files
warm_recent() {
    echo -e "\n${BLUE}Strategy 4: Recently Modified Files${NC}"
    echo "Caching files modified in the last 7 days..."
    
    # Find recently modified files
    find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.java" -o -name "*.php" \) \
        -mtime -7 -print0 | while IFS= read -r -d '' file; do
        fortris cache "$file"
    done
}

# Strategy 5: Warm based on git history
warm_git_hotspots() {
    echo -e "\n${BLUE}Strategy 5: Git Hotspots${NC}"
    
    if [ ! -d ".git" ]; then
        echo -e "${YELLOW}Not a git repository. Skipping git-based warming.${NC}"
        return
    fi
    
    echo "Analyzing git history for frequently changed files..."
    
    # Get most frequently changed files in the last 30 days
    git log --since="30 days ago" --pretty=format: --name-only | \
        sort | uniq -c | sort -rn | head -50 | \
        awk '{print $2}' | while read file; do
        if [ -f "$file" ]; then
            fortris cache "$file"
        fi
    done
}

# Strategy 6: Warm external dependencies
warm_dependencies() {
    echo -e "\n${BLUE}Strategy 6: External Dependencies${NC}"
    echo "Caching dependency and configuration files..."
    
    fortris warm \
        "**/package*.json" "**/yarn.lock" "**/package-lock.json" \
        "**/requirements*.txt" "**/Pipfile*" "**/poetry.lock" \
        "**/pom.xml" "**/build.gradle" "**/gradle.properties" \
        "**/composer.json" "**/composer.lock" \
        "**/Gemfile*" "**/Cargo.toml" "**/go.mod"
}

# Strategy 7: Custom security patterns
warm_custom_patterns() {
    echo -e "\n${BLUE}Strategy 7: Custom Security Patterns${NC}"
    echo "Enter custom file patterns to cache (comma-separated):"
    echo "Example: **/login*.py,**/payment*.js,**/admin*.php"
    
    read -p "Patterns: " patterns
    
    if [ -n "$patterns" ]; then
        IFS=',' read -ra PATTERN_ARRAY <<< "$patterns"
        fortris warm "${PATTERN_ARRAY[@]}"
    fi
}

# Main menu
show_menu() {
    echo -e "\n${GREEN}Select warming strategy:${NC}"
    echo "1) High-risk files (recommended for security)"
    echo "2) By technology stack"
    echo "3) By project structure"
    echo "4) Recently modified files"
    echo "5) Git hotspots"
    echo "6) External dependencies"
    echo "7) Custom patterns"
    echo "8) Run all strategies"
    echo "9) Exit"
}

# Main loop
while true; do
    show_menu
    read -p "Enter choice (1-9): " choice
    
    case $choice in
        1) warm_high_risk ;;
        2) warm_by_stack ;;
        3) warm_by_structure ;;
        4) warm_recent ;;
        5) warm_git_hotspots ;;
        6) warm_dependencies ;;
        7) warm_custom_patterns ;;
        8)
            warm_high_risk
            warm_by_structure
            warm_recent
            warm_dependencies
            ;;
        9)
            echo -e "\n${GREEN}Fortris cache warming complete!${NC}"
            echo "Run 'fortris report' to see security analysis results."
            exit 0
            ;;
        *)
            echo -e "${YELLOW}Invalid choice. Please try again.${NC}"
            ;;
    esac
done