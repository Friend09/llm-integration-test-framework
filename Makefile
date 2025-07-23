.PHONY: install clean

install:
	@echo "Installing dependencies using uv..."
	uv pip install -r requirements.txt

clean:
	@echo "Cleaning up..."
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf *.egg-info
	rm -rf dist
	rm -rf build
