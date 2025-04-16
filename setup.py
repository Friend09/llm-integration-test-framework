from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="llm-test-framework",
    version="0.1.0",
    author="LLM Integration Test Framework Team",
    author_email="info@example.com",
    description="LLM Integration Testing Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Friend09/llm-smoke-test-framework",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "openai>=1.0.0",
        "gitpython>=3.1.0",
        "jinja2>=3.0.0",
        "pytest>=7.0.0",
        "python-dotenv>=1.0.0",
        "typer>=0.9.0",
        "rich>=13.0.0",
        "networkx>=3.0",
        "requests>=2.28.0",
        "tiktoken>=0.3.0",
        "tenacity>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "llm-test=src.cli.main:main",
            "llm-quick-test=src.test_end_to_end:run_analysis",
        ],
    },
    package_data={
        "src.reporting.templates": ["*.html", "*.css", "*.js"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
    ],
)
