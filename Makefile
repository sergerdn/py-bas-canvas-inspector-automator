
poetry_install:
	poetry self add poetry-plugin-up@latest
	poetry install

poetry_upgrade:
	poetry up --latest
	poetry update
	poetry show --outdated

lint_fix:
	poetry run black cmd_worker.py py_bas_canvas_inspector_automator/ tests/
	poetry run isort cmd_worker.py py_bas_canvas_inspector_automator/ tests/

lint:
	poetry check
	poetry run mypy cmd_worker.py py_bas_canvas_inspector_automator/ tests/ || echo ""
	poetry run flake8 cmd_worker.py py_bas_canvas_inspector_automator/ tests/ || echo ""
	pylint --load-plugins pylint_pydantic cmd_worker.py py_bas_canvas_inspector_automator/ tests/ || echo ""

run_worker:
	rm ./docs/screenshots/*.png || echo ""
	poetry run python cmd_worker.py
	git add ./docs/screenshots/*
