"""Repository scanner module.

This module provides functionality to scan and analyze code repositories,
extracting information about files, dependencies, and structure.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from git import Repo

from config.settings import ScannerConfig


@dataclass
class CodeFile:
    """Represents a source code file with metadata."""
    path: Path
    content: str
    language: str
    imports: List[str] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)
    is_test_file: bool = False


@dataclass
class RepositoryStructure:
    """Represents the structure and content of a code repository."""
    files: Dict[str, CodeFile] = field(default_factory=dict)
    entry_points: List[str] = field(default_factory=list)
    dependencies: Dict[str, Set[str]] = field(default_factory=dict)
    language_stats: Dict[str, int] = field(default_factory=dict)
    test_files: List[str] = field(default_factory=list)


class RepositoryScanner:
    """Scans a Git repository and extracts code files and their relationships."""

    # Language detection based on file extensions
    LANGUAGE_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.kt': 'kotlin',
        '.cs': 'csharp',
        '.go': 'go',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.rs': 'rust',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c'
    }

    # Patterns for identifying test files by name
    TEST_FILE_PATTERNS = [
        '*test*.py', 'test_*.py', '*Test*.java', '*Test.java',
        '*test*.js', '*test*.ts', '*spec.js', '*spec.ts',
        '*_test.go', '*_test.rb', '*Test.php', '*Test.cs'
    ]

    def __init__(self, repo_url: str, config: ScannerConfig):
        """
        Initialize repository scanner.

        Args:
            repo_url: URL to the Git repository
            config: Scanner configuration
        """
        self.repo_url = repo_url
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def scan(self) -> RepositoryStructure:
        """
        Scan the repository and return its structure.

        Returns:
            RepositoryStructure: Repository structure with files and their relationships.

        Raises:
            Exception: If there is an error scanning the repository.
        """
        self.logger.info(f"Scanning repository: {self.repo_url}")

        try:
            repo_dir = await self._clone_repository()
            return await self._scan_directory(repo_dir)
        except Exception as e:
            self.logger.error(f"Error scanning repository: {str(e)}")
            raise

    async def _clone_repository(self) -> Path:
        """
        Clone the repository to a temporary directory.

        Returns:
            Path: Path to the cloned repository.

        Raises:
            Exception: If there is an error cloning the repository.
        """
        # Create target directory if it doesn't exist
        self.config.temp_dir.mkdir(parents=True, exist_ok=True)

        # Extract repository name from URL
        repo_name = self.repo_url.split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]

        target_path = self.config.temp_dir / repo_name

        # If directory exists, pull latest changes. Otherwise, clone.
        if target_path.exists():
            self.logger.info(f"Repository already exists at {target_path}, pulling latest changes")
            try:
                repo = Repo(target_path)
                origin = repo.remotes.origin
                origin.pull()
            except Exception as e:
                # If pull fails, remove and re-clone
                self.logger.warning(f"Failed to pull changes, re-cloning: {str(e)}")
                if target_path.exists():
                    import shutil
                    shutil.rmtree(target_path)
                Repo.clone_from(self.repo_url, target_path)
        else:
            self.logger.info(f"Cloning repository to {target_path}")
            Repo.clone_from(self.repo_url, target_path)

        return target_path

    async def _scan_directory(self, directory: Path) -> RepositoryStructure:
        """
        Scan a directory recursively and extract information about files.

        Args:
            directory: Path to the directory to scan.

        Returns:
            RepositoryStructure: Repository structure with files and their relationships.
        """
        repo_structure = RepositoryStructure()

        # Process files in parallel for better performance
        tasks = []

        # Walk through the directory
        for path in directory.glob("**/*"):
            # Skip directories and excluded patterns
            if not path.is_file() or self._is_excluded(path, directory):
                continue

            # Skip files that exceed the size limit
            if path.stat().st_size > self.config.max_file_size:
                self.logger.warning(f"Skipping file larger than {self.config.max_file_size} bytes: {path}")
                continue

            # Process file
            tasks.append(self._process_file(path, directory, repo_structure))

        # Wait for all file processing tasks to complete
        await asyncio.gather(*tasks)

        # Find dependencies between files
        await self._extract_dependencies(repo_structure)

        # Calculate language statistics
        for file in repo_structure.files.values():
            repo_structure.language_stats[file.language] = repo_structure.language_stats.get(file.language, 0) + 1

        return repo_structure

    def _is_excluded(self, path: Path, base_dir: Path) -> bool:
        """
        Check if a file should be excluded based on configured patterns.

        Args:
            path: Path to the file to check.
            base_dir: Base directory of the repository.

        Returns:
            bool: True if the file should be excluded, False otherwise.
        """
        relative_path = path.relative_to(base_dir)

        # Check if any part of the path matches an exclude pattern
        path_str = str(relative_path)
        for pattern in self.config.exclude_patterns:
            if pattern in path_str:
                return True

        return False

    async def _process_file(self, path: Path, base_dir: Path, repo_structure: RepositoryStructure) -> None:
        """
        Process a single file and extract information about it.

        Args:
            path: Path to the file to process.
            base_dir: Base directory of the repository.
            repo_structure: Repository structure to update.
        """
        relative_path = path.relative_to(base_dir)
        path_str = str(relative_path)

        # Determine the language based on file extension
        language = self._detect_language(path)

        # Skip if we don't support this file type
        if not language:
            return

        # Read the file content
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"Error reading file {path}: {str(e)}")
            return

        # Check if it's a test file
        is_test_file = self._is_test_file(path_str)

        # Create CodeFile object
        code_file = CodeFile(
            path=relative_path,
            content=content,
            language=language,
            is_test_file=is_test_file
        )

        # Add to repository structure
        repo_structure.files[path_str] = code_file

        # Add to test files list if applicable
        if is_test_file:
            repo_structure.test_files.append(path_str)

    def _detect_language(self, path: Path) -> Optional[str]:
        """
        Detect the programming language of a file based on its extension.

        Args:
            path: Path to the file.

        Returns:
            str or None: The detected language or None if not detected.
        """
        extension = path.suffix.lower()
        return self.LANGUAGE_EXTENSIONS.get(extension)

    def _is_test_file(self, file_path: str) -> bool:
        """
        Determine if a file is a test file based on its name.

        Args:
            file_path: Path to the file.

        Returns:
            bool: True if the file is a test file, False otherwise.
        """
        # Check for test directories
        parts = file_path.split('/')
        if any(part == 'test' or part == 'tests' or part == 'spec' for part in parts):
            return True

        # Check for test file patterns
        return any(fnmatch(file_path, pattern) for pattern in self.TEST_FILE_PATTERNS)

    async def _extract_dependencies(self, repo_structure: RepositoryStructure) -> None:
        """
        Extract imports and dependencies from code files.

        Args:
            repo_structure: Repository structure to update.
        """
        # Process files in parallel for better performance
        tasks = []

        for file_path, file in repo_structure.files.items():
            if file.language == 'python':
                tasks.append(self._extract_python_imports(file))
            elif file.language in ('javascript', 'typescript'):
                tasks.append(self._extract_js_imports(file))
            elif file.language == 'java':
                tasks.append(self._extract_java_imports(file))

        # Wait for all import extraction tasks to complete
        await asyncio.gather(*tasks)

        # Build a mapping of module/package names to files
        module_to_file = {}
        for path, file in repo_structure.files.items():
            # For Python, use the file path without extension as a potential module
            if file.language == 'python':
                module_path = str(file.path.with_suffix(''))
                module_parts = module_path.split('/')

                # Add all possible import paths
                for i in range(len(module_parts)):
                    module_name = '.'.join(module_parts[i:])
                    if module_name:
                        module_to_file[module_name] = path

        # Map imports to actual files in the repository
        for file_path, file in repo_structure.files.items():
            for imported in file.imports:
                if imported in module_to_file:
                    target_file = module_to_file[imported]
                    file.dependencies.add(target_file)

                    # Update repository dependencies
                    if file_path not in repo_structure.dependencies:
                        repo_structure.dependencies[file_path] = set()
                    repo_structure.dependencies[file_path].add(target_file)

    async def _extract_python_imports(self, code_file: CodeFile) -> None:
        """
        Extract imports from Python code.

        Args:
            code_file: CodeFile object to update.
        """
        import re

        # Match 'import x' and 'from x import y'
        import_patterns = [
            r'^import\s+([\w\.]+)',
            r'^from\s+([\w\.]+)\s+import'
        ]

        for pattern in import_patterns:
            for match in re.finditer(pattern, code_file.content, re.MULTILINE):
                imported_module = match.group(1)
                # Only consider project imports (no standard library)
                if '.' in imported_module and not imported_module.startswith('.'):
                    # Get the top-level module
                    top_module = imported_module.split('.')[0]
                    code_file.imports.append(top_module)
                elif imported_module.startswith('.'):
                    # Relative import - more complex to resolve
                    # We could implement this in a future version
                    pass
                else:
                    code_file.imports.append(imported_module)

    async def _extract_js_imports(self, code_file: CodeFile) -> None:
        """
        Extract imports from JavaScript/TypeScript code.

        Args:
            code_file: CodeFile object to update.
        """
        import re

        # Match ES6 imports
        import_patterns = [
            r'import\s+.*\s+from\s+[\'"]([\.\/\w-]+)[\'"]',
            r'import\s+[\'"]([\.\/\w-]+)[\'"]',
            r'require\s*\(\s*[\'"]([\.\/\w-]+)[\'"]\s*\)'
        ]

        for pattern in import_patterns:
            for match in re.finditer(pattern, code_file.content):
                imported_module = match.group(1)

                # Skip node_modules
                if not imported_module.startswith('.') and not imported_module.startswith('/'):
                    continue

                code_file.imports.append(imported_module)

    async def _extract_java_imports(self, code_file: CodeFile) -> None:
        """
        Extract imports from Java code.

        Args:
            code_file: CodeFile object to update.
        """
        import re

        # Match Java imports
        import_pattern = r'^import\s+([\w\.]+);'

        for match in re.finditer(import_pattern, code_file.content, re.MULTILINE):
            imported_module = match.group(1)

            # Extract the package name
            if '.' in imported_module:
                package = '.'.join(imported_module.split('.')[:-1])
                code_file.imports.append(package)
