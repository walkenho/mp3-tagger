FROM python:3.8-slim-buster
LABEL maintainer="Jessica Walkenhorst"
LABEL description="mp3 tagger"


ARG EXPECTED_PYTHON_VERSION="3.8"
# This version is current default in 3.8.6
ARG PIP_VERSION="21.2.1"
# Latest stable at time of writing
ARG POETRY_VERSION="1.1.6"

RUN pip3 install -q "pip==$PIP_VERSION"

# We want Poetry installed, of course
RUN pip3 install -q "poetry==$POETRY_VERSION"

WORKDIR /home/

COPY pyproject.toml poetry.lock tagger.py ./
COPY src ./src/

RUN poetry install --no-dev

RUN mkdir data

EXPOSE 8501

# This is more useful for a builder
ENTRYPOINT ["poetry", "run", "streamlit", "run", "tagger.py"]
