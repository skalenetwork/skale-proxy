#!/usr/bin/env bash

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install codecov pytest-cov