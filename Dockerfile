FROM python:3.8-slim-buster
LABEL maintainer="Jessica Walkenhorst"
LABEL description="MP3 Tagger"

ARG PIP_VERSION="21.2.1"
ARG POETRY_VERSION="1.1.6"

RUN pip3 install -q "pip==$PIP_VERSION"
RUN pip3 install -q "poetry==$POETRY_VERSION"

WORKDIR /home/

COPY pyproject.toml poetry.lock tagger.py ./
COPY src ./src/

RUN poetry install --no-dev

RUN mkdir data

EXPOSE 8501

ENTRYPOINT ["poetry", "run", "streamlit", "run", "tagger.py"]
