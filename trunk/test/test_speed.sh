#!/bin/sh

# Retrieve corpus data if not present.
python3 prepare.py

# Run once to populate OS cache.
python process_once.py

# Timed process
echo "Using Python 2:"
time python process_once.py

echo "Using Python 3:"
time python3 process_once.py

