#!/bin/bash
CRED_DIR="$HOME/.claude/.credentials"

case "$1" in
    init)
        mkdir -p "$CRED_DIR" && chmod 700 "$CRED_DIR"
        if [ ! -f "$CRED_DIR/.master_key" ]; then
            openssl rand -base64 32 > "$CRED_DIR/.master_key"
            chmod 600 "$CRED_DIR/.master_key"
            echo "✅ Master key created - BACK THIS UP!"
        fi
        ;;
    set)
        [ ! -f "$CRED_DIR/.master_key" ] && $0 init
        echo "$3" | openssl enc -aes-256-cbc -a -salt -pass file:"$CRED_DIR/.master_key" -out "$CRED_DIR/$2.enc"
        chmod 600 "$CRED_DIR/$2.enc"
        echo "✅ Saved: $2"
        ;;
    get)
        [ -f "$CRED_DIR/$2.enc" ] && openssl enc -aes-256-cbc -d -a -pass file:"$CRED_DIR/.master_key" -in "$CRED_DIR/$2.enc"
        ;;
    list)
        ls -1 "$CRED_DIR"/*.enc 2>/dev/null | xargs -I{} basename {} .enc
        ;;
esac
