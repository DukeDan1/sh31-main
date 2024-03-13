#!/bin/sh
project_path="$(dirname "$(realpath "$0")")/conversation_analyzer"
git clean -xf conversation_analyzer/media
rm -f "$project_path/analyzer/migrations/0"*'.py'
rm -f "$project_path/db.sqlite3"
python "$project_path/manage.py" makemigrations
python "$project_path/manage.py" migrate
python "$project_path/populate_analyzer.py" && echo 'Population Done.'
