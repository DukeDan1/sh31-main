#!/bin/bash
while true; do
    echo "Starting server..."
    venv/bin/python conversation_analyzer/manage.py runserver 15000
    echo "Server exited. Respawning.."
    sleep 5
done
