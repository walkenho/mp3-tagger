#!/bin/bash
poetry run isort src/
poetry run flake8 src/
