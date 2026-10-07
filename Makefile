RESET := \033[0m
BOLD := \033[1m
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
BLUE := \033[34m
WHITE := \033[97m

PROJECT := fly-in

.PHONY: install install-req run debug clean lint lint-strict help

help:
	@printf "\n$(BOLD)$(CYAN)╔══════════════════════════════════════╗$(RESET)\n"
	@printf "$(BOLD)$(CYAN)║ $(WHITE)$(PROJECT)$(CYAN) ║$(RESET)\n"
	@printf "$(BOLD)$(CYAN)╚══════════════════════════════════════╝$(RESET)\n\n"
	@printf "$(GREEN)make install$(RESET) Install dependencies with Poetry\n"
	@printf "$(GREEN)make install-req$(RESET) Create venv and install requirements.txt\n"
	@printf "$(GREEN)make run$(RESET) Run the project\n"
	@printf "$(GREEN)make debug$(RESET) Run the project with pdb\n"
	@printf "$(GREEN)make lint$(RESET) Run flake8 and mypy\n"
	@printf "$(GREEN)make lint-strict$(RESET) Run mypy with --strict\n"
	@printf "$(GREEN)make clean$(RESET) Remove Python caches\n\n"

install:
	@printf "$(BOLD)$(CYAN)→ Installing dependencies...$(RESET)\n"
	@poetry install
	@printf "$(GREEN)✓ Dependencies installed.$(RESET)\n"

install-req:
	@printf "$(BOLD)$(CYAN)→ Creating virtual environment...$(RESET)\n"
	@python3 -m venv venv
	@printf "$(BOLD)$(CYAN)→ Installing requirements...$(RESET)\n"
	@source ./venv/bin/activate && pip install -r requirements.txt
	@printf "$(GREEN)✓ Ready to run.$(RESET)\n"

run: install
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		printf "$(RED)✗ Error: not running inside a virtual environment.$(RESET)\n"; \
		printf "$(YELLOW) Activate your venv first:\n  source venv/bin/activate\n  or source $$(poetry env activate)$(RESET)\n"; \
		exit 1; \
	fi
	@printf "$(GREEN)✓ Virtual environment detected: $$VIRTUAL_ENV$(RESET)\n"
	@printf "$(BOLD)$(CYAN)→ Starting $(PROJECT)...$(RESET)\n\n"
	@python3 main.py

dev:
	python3 main.py maps/easy/01_linear_path.txt 2>log.txt

debug: install
	@printf "$(BOLD)$(YELLOW)→ Starting debugger...$(RESET)\n"
	@python3 -m pdb main.py

clean:
	@printf "$(BOLD)$(RED)→ Cleaning project...$(RESET)\n"
	@find . -type d -name "pycache" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@printf "$(GREEN)✓ Project cleaned.$(RESET)\n"

lint:
	@printf "$(BOLD)$(BLUE)→ Running flake8...$(RESET)\n"
	@python3 -m flake8 .
	@printf "$(GREEN)✓ flake8 passed.$(RESET)\n"
	@printf "$(BOLD)$(BLUE)→ Running mypy...$(RESET)\n"
	@python3 -m mypy .
	--warn-return-any
	--warn-unused-ignores
	--ignore-missing-imports
	--disallow-untyped-defs
	--check-untyped-defs
	@printf "$(GREEN)✓ mypy passed.$(RESET)\n"

lint-strict: lint
	@printf "$(BOLD)$(YELLOW)→ Running strict mypy...$(RESET)\n"
	@python3 -m mypy . --strict
	@printf "$(GREEN)✓ Strict mypy passed.$(RESET)\n"