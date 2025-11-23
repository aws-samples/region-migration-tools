#!/bin/bash
# Cleanup script for multi-region planner analysis results

echo "Cleaning up analysis results..."

# Remove all files except .gitkeep
find analysis_results -type f ! -name '.gitkeep' -delete

echo "Analysis results directory cleaned. Ready for new analysis."
