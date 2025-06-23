#!/bin/bash
# Move project from Windows to WSL native filesystem

PROJECT="${1:-$(basename $PWD)}"
WIN_PATH="${2:-$PWD}"

if [[ "$WIN_PATH" == /mnt/c/* ]]; then
    echo "Moving $PROJECT to native filesystem..."
    cp -r "$WIN_PATH" ~/projects/
    echo "✅ Moved to ~/projects/$PROJECT"
    echo "   Performance will be significantly better!"
    echo "   Windows symlink: mklink /D C:\\WSL-Projects\\$PROJECT \\\\wsl$\\Ubuntu\\home\\$USER\\projects\\$PROJECT"
else
    echo "Already on native filesystem"
fi
