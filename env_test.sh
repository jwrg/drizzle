#!/bin/bash

# This shell script activates the virtual environment
# and sets up some environment variables to set up the
# application for testing.

source ./venv/bin/activate
export DRIZZLE_TEST_CONFIG=test/config.py
