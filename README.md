# Conversation Intelligence Analyzer

[![coverage report](https://stgit.dcs.gla.ac.uk/team-project-h/2023/sh31/sh31-main/badges/main/coverage.svg)](https://stgit.dcs.gla.ac.uk/team-project-h/2023/sh31/sh31-main/-/commits/main) 

## About Project

Conversation Intelligence Analyser revolutionises the way you understand and interpret chat interactions. Our cutting-edge platform meticulously analyses chat logs, transforming them into insightful profiles and comprehensive analyses for entire conversations. We specialise in producing detailed graphs and assigning risk/sentiment scores, offering an unparalleled depth of understanding. Whether you're a business looking to enhance customer service, a team aiming to improve communication, or an individual seeking insights into chat dynamics, our tool provides the clarity and perspective needed to make informed decisions. Dive into the essence of your conversations with Conversation Intelligence Analyser and unlock the power of data-driven analysis!

## Installation and Deployment

For all installation methods, `python 3.11` must be installed along with `pip`, first method is recommended as an one-click installation and deployment.

We recommend using a machine that has at least 8 GB RAM and 30 GB free storage space.

### Install from GitHub repository
Run the following commands on your machine:
```
sudo apt update -y && sudo apt upgrade -y
sudo apt install unzip python-is-python3 python3.11-venv git wget -y
git clone https://github.com/DukeDan1/sh31-main.git && cd sh31-main
chmod +x deploy.sh start.sh db-clean.sh change-openai.sh
./deploy.sh
```

### Install from zip file (`sh31-main.zip`)
For a clean install, please upload the `sh31-main.zip` file to the server, and run the following commands while in the directory that the `sh31-main.zip` file is in.
```
sudo apt update -y && sudo apt upgrade -y
sudo apt install unzip python-is-python3 python3.11-venv git wget -y
unzip sh31-main.zip && cd sh31-main
chmod +x deploy.sh start.sh db-clean.sh change-openai.sh
./deploy.sh
```

### With tarball:
If you have bash, git, wget, unzip, Python 3.11, pip, and Python venv installed then you can simply run the `./deploy.sh` in the base project directory and the server will initialise and start automatically.

### With access to University GitLab servers:
Ensure you have Git and Git LFS installed and follow the following steps:
  1. Run `git clone https://stgit.dcs.gla.ac.uk/team-project-h/2023/sh31/sh31-main.git && cd sh31-main`
  1. Run `pip install -r requirements.txt` to install all dependencies.
  1. Run `git lfs pull` to pull all large NLP models.
  1. Run `./db-clean.sh` with this directory as the working directory.
  1. Run `./manage.py conversation_analyzer/manage.py runserver` to start the server.

If the server is being accessed externally, `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in `conversation_analyzer/conversation_analyzer/settings.py` should be changed to include the domain of the server.

## Authors and acknowledgment

This project is created by the SH31 Team.

## License

This project is licensed under MIT license, which is detailed in the `LICENSE` file. Material icons are licensed separately under the Apache license, which is detailed in the `MATERIAL_ICONS_LICENSE` file.

## Changing OpenAI key

To change the OpenAI key, run `./change-openai.sh` from the base project directory.

## Project status

This project is tested and there are no bugs that the SH31 Team is aware of.

## Walkthrough

[Project Walkthrough Document](Walkthrough.md)