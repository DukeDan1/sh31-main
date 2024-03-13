FROM pytorch/pytorch:2.1.1-cuda12.1-cudnn8-runtime

RUN apt-get update && DEBIAN_FRONTEND='noninteractive' apt-get install --yes curl
RUN curl https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
RUN . ~/.bashrc && nvm install --latest-npm 21.6.0
WORKDIR /packages
RUN . ~/.bashrc && npm init --yes
RUN . ~/.bashrc && npm install eslint eslint-config-google
COPY requirements.txt requirements.txt
COPY test_requirements.txt test_requirements.txt
RUN python -m pip install --requirement requirements.txt \
    && python -m pip install --requirement test_requirements.txt \
    && python -m pip install flair
