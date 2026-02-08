.PHONY: setup clean install test run run-api test-api help

# Virtual environment directory
VENV_DIR = venv
PYTHON = python3
PIP = $(VENV_DIR)/bin/pip
VENV_PYTHON = $(VENV_DIR)/bin/python

help:
	@echo "Available targets:"
	@echo "  make setup     - Remove existing venv, create new one, and install dependencies"
	@echo "  make clean     - Remove virtual environment"
	@echo "  make run-api   - Start the API server"
	@echo "  make test-api  - Run API test script"

setup: clean
	@echo "Creating new virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo ""
	@echo "✓ Virtual environment created and dependencies installed!"
	@echo "To activate: source $(VENV_DIR)/bin/activate"

clean:
	@echo "Removing virtual environment..."
	@rm -rf $(VENV_DIR)
	@echo "✓ Virtual environment removed"

run-api:
	@echo "Starting API server..."
	@echo "Server will be available at http://localhost:5000"
	@echo "Press Ctrl+C to stop"
	$(VENV_PYTHON) api/app.py

test-api:
	@echo "Running API tests..."
	@./test_api.sh