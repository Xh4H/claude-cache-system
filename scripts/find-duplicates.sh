#!/bin/bash
# Find duplicate directories and analyze structure

CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
OUTPUT_FILE="$CLAUDE_HOME/STRUCTURE_ANALYSIS.md"

echo "🔍 Analyzing directory structure and finding duplicates..."

# Function to find directories with similar names
find_duplicate_dirs() {
    echo "## Duplicate Directory Analysis" > "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "### Directories with Similar Names:" >> "$OUTPUT_FILE"
    
    # Find all directories and group by base name
    find "$CLAUDE_HOME" -type d -name "*" 2>/dev/null | while read dir; do
        basename "$dir"
    done | sort | uniq -c | sort -nr | while read count name; do
        if [ "$count" -gt 1 ]; then
            echo "" >> "$OUTPUT_FILE"
            echo "**$name** appears $count times:" >> "$OUTPUT_FILE"
            find "$CLAUDE_HOME" -type d -name "$name" 2>/dev/null | while read path; do
                echo "- $path" >> "$OUTPUT_FILE"
            done
        fi
    done
}

# Function to analyze file duplicates
find_duplicate_files() {
    echo "" >> "$OUTPUT_FILE"
    echo "### Files with Similar Names:" >> "$OUTPUT_FILE"
    
    # Group files by name pattern
    declare -A file_groups
    
    # Check for cleanup scripts
    echo "" >> "$OUTPUT_FILE"
    echo "**Cleanup scripts:**" >> "$OUTPUT_FILE"
    find "$CLAUDE_HOME" -name "*clean*.sh" -type f 2>/dev/null | while read f; do
        echo "- $f" >> "$OUTPUT_FILE"
    done
    
    # Check for config files
    echo "" >> "$OUTPUT_FILE"
    echo "**Config files:**" >> "$OUTPUT_FILE"
    find "$CLAUDE_HOME" -name "*.conf" -o -name "config.*" -o -name "settings.*" -type f 2>/dev/null | while read f; do
        echo "- $f" >> "$OUTPUT_FILE"
    done
    
    # Check for knowledge scripts
    echo "" >> "$OUTPUT_FILE"
    echo "**Knowledge scripts:**" >> "$OUTPUT_FILE"
    find "$CLAUDE_HOME" -name "*knowledge*.sh" -type f 2>/dev/null | while read f; do
        echo "- $f" >> "$OUTPUT_FILE"
    done
    
    # Check for session scripts
    echo "" >> "$OUTPUT_FILE"
    echo "**Session scripts:**" >> "$OUTPUT_FILE"
    find "$CLAUDE_HOME" -name "*session*.sh" -type f 2>/dev/null | while read f; do
        echo "- $f" >> "$OUTPUT_FILE"
    done
}

# Function to create full directory tree
create_directory_tree() {
    echo "" >> "$OUTPUT_FILE"
    echo "## Complete Directory Structure" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo '```' >> "$OUTPUT_FILE"
    
    # Use tree if available, otherwise custom function
    if command -v tree &> /dev/null; then
        tree -a -I '.git' "$CLAUDE_HOME" >> "$OUTPUT_FILE"
    else
        # Custom tree function
        print_tree() {
            local dir="$1"
            local prefix="$2"
            local last="$3"
            
            local name=$(basename "$dir")
            echo "${prefix}${last}${name}" >> "$OUTPUT_FILE"
            
            # Update prefix for children
            if [ "$last" = "└── " ]; then
                prefix="${prefix}    "
            else
                prefix="${prefix}│   "
            fi
            
            # Count children
            local count=$(find "$dir" -maxdepth 1 -mindepth 1 2>/dev/null | wc -l)
            local current=0
            
            # Print children
            find "$dir" -maxdepth 1 -mindepth 1 2>/dev/null | sort | while read child; do
                ((current++))
                if [ $current -eq $count ]; then
                    print_tree "$child" "$prefix" "└── "
                else
                    print_tree "$child" "$prefix" "├── "
                fi
            done
        }
        
        print_tree "$CLAUDE_HOME" "" ""
    fi
    
    echo '```' >> "$OUTPUT_FILE"
}

# Function to analyze directory purposes
analyze_directory_purposes() {
    echo "" >> "$OUTPUT_FILE"
    echo "## Directory Purpose Analysis" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    # Check each major directory
    for dir in "$CLAUDE_HOME"/*; do
        if [ -d "$dir" ]; then
            local name=$(basename "$dir")
            local file_count=$(find "$dir" -type f 2>/dev/null | wc -l)
            local size=$(du -sh "$dir" 2>/dev/null | cut -f1)
            
            echo "### $name/" >> "$OUTPUT_FILE"
            echo "- Files: $file_count" >> "$OUTPUT_FILE"
            echo "- Size: $size" >> "$OUTPUT_FILE"
            
            # Analyze content
            case "$name" in
                scripts)
                    echo "- Purpose: Executable scripts" >> "$OUTPUT_FILE"
                    echo "- Subdirs: $(find "$dir" -mindepth 1 -maxdepth 1 -type d | wc -l)" >> "$OUTPUT_FILE"
                    ;;
                config)
                    echo "- Purpose: Configuration files" >> "$OUTPUT_FILE"
                    echo "- JSON files: $(find "$dir" -name "*.json" | wc -l)" >> "$OUTPUT_FILE"
                    echo "- Conf files: $(find "$dir" -name "*.conf" | wc -l)" >> "$OUTPUT_FILE"
                    ;;
                data)
                    echo "- Purpose: Application data" >> "$OUTPUT_FILE"
                    echo "- Telemetry: $([ -d "$dir/telemetry" ] && echo "Yes" || echo "No")" >> "$OUTPUT_FILE"
                    ;;
                *)
                    echo "- Purpose: $(
                        if [ -f "$dir/.description" ]; then
                            cat "$dir/.description"
                        else
                            echo "Unknown/Mixed"
                        fi
                    )" >> "$OUTPUT_FILE"
                    ;;
            esac
            echo "" >> "$OUTPUT_FILE"
        fi
    done
}

# Function to find redundant/empty directories
find_redundant_dirs() {
    echo "## Redundant/Empty Directories" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    echo "### Empty directories:" >> "$OUTPUT_FILE"
    find "$CLAUDE_HOME" -type d -empty 2>/dev/null | while read dir; do
        echo "- $dir" >> "$OUTPUT_FILE"
    done
    
    echo "" >> "$OUTPUT_FILE"
    echo "### Directories with only hidden files:" >> "$OUTPUT_FILE"
    find "$CLAUDE_HOME" -type d 2>/dev/null | while read dir; do
        local visible=$(find "$dir" -maxdepth 1 -name "[!.]*" 2>/dev/null | wc -l)
        local hidden=$(find "$dir" -maxdepth 1 -name ".*" -not -name "." -not -name ".." 2>/dev/null | wc -l)
        if [ $visible -eq 0 ] && [ $hidden -gt 0 ]; then
            echo "- $dir (hidden: $hidden)" >> "$OUTPUT_FILE"
        fi
    done
}

# Function to create size analysis
analyze_sizes() {
    echo "" >> "$OUTPUT_FILE"
    echo "## Size Analysis" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    echo "### Top 10 largest directories:" >> "$OUTPUT_FILE"
    du -sh "$CLAUDE_HOME"/* 2>/dev/null | sort -hr | head -10 | while read size path; do
        echo "- $size $(basename "$path")" >> "$OUTPUT_FILE"
    done
    
    echo "" >> "$OUTPUT_FILE"
    echo "### Top 10 largest files:" >> "$OUTPUT_FILE"
    find "$CLAUDE_HOME" -type f -exec du -h {} + 2>/dev/null | sort -hr | head -10 | while read size path; do
        echo "- $size $(basename "$path")" >> "$OUTPUT_FILE"
    done
}

# Main execution
echo "# Claude Directory Structure Analysis" > "$OUTPUT_FILE"
echo "Generated: $(date)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

find_duplicate_dirs
find_duplicate_files
create_directory_tree
analyze_directory_purposes
find_redundant_dirs
analyze_sizes

# Summary
echo "" >> "$OUTPUT_FILE"
echo "## Summary Statistics" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "- Total directories: $(find "$CLAUDE_HOME" -type d | wc -l)" >> "$OUTPUT_FILE"
echo "- Total files: $(find "$CLAUDE_HOME" -type f | wc -l)" >> "$OUTPUT_FILE"
echo "- Total size: $(du -sh "$CLAUDE_HOME" | cut -f1)" >> "$OUTPUT_FILE"
echo "- Script files: $(find "$CLAUDE_HOME" -name "*.sh" | wc -l)" >> "$OUTPUT_FILE"
echo "- Config files: $(find "$CLAUDE_HOME" -name "*.json" -o -name "*.conf" | wc -l)" >> "$OUTPUT_FILE"

echo "✅ Analysis complete! Results saved to: $OUTPUT_FILE"
echo ""
echo "📊 Quick summary:"
find "$CLAUDE_HOME" -type d -name "*" | basename -a $(cat) | sort | uniq -c | sort -nr | head -5 | while read count name; do
    [ $count -gt 1 ] && echo "  - '$name' directory appears $count times"
done