#!/bin/bash
project_path="$(dirname "$(realpath "$0")")/conversation_analyzer"
base_path="$(dirname "$(realpath "$0")")"
# Ask user for OpenAI key
read -p "Enter your OpenAI key, or type 'no' to continue without an OpenAI key: " openai_key
if [ -z "$openai_key" ]; then
    echo "OpenAI key is required."
    exit 1
elif [ "$openai_key" != "no" ]; then
    echo "OPENAI_API_KEY='$openai_key'" > "$project_path"/.env
    echo "OpenAI key saved."
else
    echo 'OPENAI API key not provided. Some functionality will not work.'
fi

python -m venv "$base_path"/venv
source "$base_path"/venv/bin/activate

# Install dependencies
if ! pip install -r requirements.txt ; then
    echo "Failed to install dependencies."
    exit 1
fi

if ! pip install flair ; then
    echo "Failed to install flair."
    exit 1
fi

echo "Getting NLP files. These might take some time to download..."

if ! wget https://sas.dukedan.uk/nlp-files/flair.zip -O "$base_path"/flair.zip ; then
    echo "Failed to download flair files."
    exit 1
fi

if ! wget https://sas.dukedan.uk/nlp-files/resources.zip -O "$base_path"/resources.zip ; then
    echo "Failed to download resources files."
    exit 1
fi


echo "Unzipping NLP files..."

if ! unzip "$base_path"/flair.zip ; then
    echo "Failed to unzip flair files."
    exit 1
fi

if ! unzip "$base_path"/resources.zip ; then
    echo "Failed to unzip resources files."
    exit 1
fi

git init
"$base_path"/db-clean.sh
mkdir -p "$project_path"/media/ingestion_saves "$project_path"/media/uploaded_documents
echo "Installed. Running server..."
"$base_path"/venv/bin/python "$project_path"/manage.py runserver
