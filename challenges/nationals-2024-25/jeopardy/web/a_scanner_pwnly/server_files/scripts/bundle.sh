#!/bin/bash

set -euxo pipefail

git archive --format=tar.gz --output=server_files.tar.gz --prefix=server_files/ HEAD .
