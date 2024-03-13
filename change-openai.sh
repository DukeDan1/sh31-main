#!/bin/bash
project_path="$(dirname "$(realpath "$0")")/conversation_analyzer"

read -p "Enter the OpenAI key you would like to use: " openai_key
if [ -z "$openai_key" ]; then
    echo "OpenAI key is required."
    exit 1
else 
    echo "OPENAI_API_KEY='$openai_key'" > "$project_path"/.env
    echo "OpenAI key saved."
fi
