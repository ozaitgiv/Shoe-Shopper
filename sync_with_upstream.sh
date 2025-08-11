#!/bin/bash

set -e  # Exit on any error

echo "Fetching from upstream..."
git fetch upstream

echo "Checking out local development branch..."
git checkout development

echo "Merging upstream/development into local development..."
git merge upstream/development

echo "Pushing updated development to fork..."
git push origin development

echo "Checking out local main branch..."
git checkout main

echo "Merging development into main..."
git merge development

echo "Pushing updated main to your fork..."
git push origin main

echo "✅ Sync complete!"
