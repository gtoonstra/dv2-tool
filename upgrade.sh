#!/bin/bash

pip-compile requirements.in --output-file requirements.txt
pip install -r requirements.txt

# comment
