#!/bin/bash
set -euxo pipefail

alembic upgrade head 
python run.py

