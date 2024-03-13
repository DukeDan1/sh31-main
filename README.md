# Conversation Intelligence Analyzer

[![coverage report](https://stgit.dcs.gla.ac.uk/team-project-h/2023/sh31/sh31-main/badges/main/coverage.svg)](https://stgit.dcs.gla.ac.uk/team-project-h/2023/sh31/sh31-main/-/commits/main) 

## About Project

Conversation Intelligence Analyser revolutionises the way you understand and interpret chat interactions. Our cutting-edge platform meticulously analyses chat logs, transforming them into insightful profiles and comprehensive analyses for entire conversations. We specialise in producing detailed graphs and assigning risk/sentiment scores, offering an unparalleled depth of understanding. Whether you're a business looking to enhance customer service, a team aiming to improve communication, or an individual seeking insights into chat dynamics, our tool provides the clarity and perspective needed to make informed decisions. Dive into the essence of your conversations with Conversation Intelligence Analyser and unlock the power of data-driven analysis!

## Installation

For all installation methods, `python 3.11` must be installed along with `pip`, first method is recommended as an one-click installation and deployment.

### With tarball (with `bash`, `wget`, and `unzip` installed):
  1. Run `./deploy.sh` in the base project directory.
  1. Everything should be downloaded and the server should start automatically.

This method has been tested with a server running Debian 12. We recommend using a server with at least 8 GB of RAM. For a clean install, please upload the `sh31-main.zip` file to the server, and run the following commands while in the directory that the `sh31-main.zip` file is in.
```
sudo apt update
sudo apt upgrade
sudo apt install unzip python-is-python3 python3.11-venv git
unzip sh31-main.zip && cd sh31-main
chmod +x deploy.sh start.sh db-clean.sh
./deploy.sh
```

### With Git access (with `git` and `git-lfs` installed):
  1. Clone this repository.
  1. Run `pip install -r requirements.txt` to install all dependencies.
  1. Run `git lfs pull` to pull all large NLP models.
  1. Run `./db-clean.sh` with this directory as the working directory.
  1. Run `./manage.py conversation_analyzer/manage.py runserver` to start the server.

If the server is being accessed externally, `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in `conversation_analyzer/conversation_analyzer/settings.py` should be changed to include the domain of the server.

## Authors and acknowledgment

This project is created by the SH31 Team.

## License

This project is licensed under MIT license, which is detailed in the `LICENSE` file. Material icons are licensed separately under the Apache license, which is detailed in the `MATERIAL_ICONS_LICENSE` file.

## Project status

This project is tested and there are no bugs that the SH31 Team is aware of.

## Walkthrough

[Project Walkthrough Document](Walkthrough.md)