#!/usr/bin/env bash


if [[ "$1" == "--fix" ]]; then
    echo "🛠️  Auto-fixing issues..."
    ruff check src/ --fix
    ruff format src/
    echo "✅ Fixes applied."
    echo "-------------------------------------"
fi

echo "🚀 Starting PyOB Validation Suite..."
EXIT_STATUS=0

echo "-------------------------------------"
echo "🧹 1. Running Ruff (Linter & Imports)..."
if ! ruff check src/ --fix; then
    echo "❌ Ruff Linter failed."
    EXIT_STATUS=1
fi

echo "-------------------------------------"
echo "🪄  2. Formatting Code with Ruff..."
if ! ruff format src/ tests/; then
    echo "❌ Ruff Formatter failed."
    EXIT_STATUS=1
fi

echo "-------------------------------------"
echo "🔎 3. Running Mypy (Type Checking)..."
if ! mypy src/ --ignore-missing-imports; then
    echo "❌ Mypy Type Checking failed."
    EXIT_STATUS=1
fi

echo "-------------------------------------"
echo "🧪 4. Running Pytest (Unit Tests)..."
if [ -d "tests" ] && [ "$(ls -A tests 2>/dev/null)" ]; then
    if ! pytest tests/; then
        echo "❌ Pytest failed."
        EXIT_STATUS=1
    fi
else
    echo "⚠️  No tests found in 'tests/' directory."
fi

echo "-------------------------------------"
if [ $EXIT_STATUS -ne 0 ]; then
    echo "🚨 Validation Suite Failed! Triggering AI rollback..."
    exit $EXIT_STATUS
else
    echo "✅ All checks passed! Patch is valid."
    exit 0
fi