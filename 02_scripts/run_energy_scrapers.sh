#!/bin/bash

echo "===== Script Started ====="
echo "Activating conda..."
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate base
echo "Conda environment activated: $CONDA_DEFAULT_ENV"

echo "Running Tesla scraper..."
python /Users/jesusortiz/Documents/projects/02_energy/02_scripts/02_tesla_data.py

echo "Running LUMA scraper..."
python /Users/jesusortiz/Documents/projects/02_energy/02_scripts/01_luma_data.py

echo "===== Script Ended ====="