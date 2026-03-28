# Contributing to font-lab

Thank you for your interest in contributing! This guide covers everything you need to get started.

## Getting started

```bash
# 1. Fork and clone the repository
git clone https://github.com/<your-username>/font-lab.git
cd font-lab

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the development server
uvicorn app.main:app --reload
```

## Running tests

```bash
pytest tests/ -v
```

All pull requests must pass the full test suite before being merged.

## Code style

- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code.
- Use descriptive variable and function names.
- Add docstrings to new public functions and classes.

## Submitting changes

1. Create a feature branch: `git checkout -b feature/my-improvement`
2. Make your changes and add tests that cover the new behaviour.
3. Run `pytest tests/ -v` and confirm all tests pass.
4. Open a pull request against `main` with a clear description of what was changed and why.

## Provenance guidelines

When contributing font sample data, please record:

- **source** — where the image came from (URL, publication, archive name, or a brief description).
- **restoration_notes** — any processing or restoration work applied to the image (e.g. "despeckled and contrast-adjusted").

These fields help reviewers understand the provenance and quality of each sample and are stored directly on the `FontSample` record.

## Licensing

By contributing to this project you agree that your contributions will be licensed under the [MIT License](LICENSE).
