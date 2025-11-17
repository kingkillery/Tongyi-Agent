"""
Setup script for Tongyi Agent CLI
"""
from setuptools import setup, find_packages
import os

# Read README for long description
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
long_description = ""
if os.path.exists(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()

# Read requirements
requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
requirements = []
if os.path.exists(requirements_path):
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="tongyi-agent",
    version="1.1.0",
    description="Interactive CLI for Tongyi Agent with Claude SDK and OpenRouter integration",
    long_description=long_description or "Interactive CLI for Tongyi Agent",
    long_description_content_type="text/markdown",
    author="Tongyi Agent Team",
    author_email="contact@tongyi-agent.com",
    url="https://github.com/tongyi-agent/tongyi-agent",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['*.md', '*.txt', '*.json'],
    },
    install_requires=requirements,
    extras_require={
        "claude-sdk": ["claude-code-sdk"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ]
    },
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "tongyi=tongyi_agent.cli:main",
            "tongyi-cli=tongyi_agent.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Utilities",
    ],
    keywords="ai cli agent tongyi claude openrouter chatbot tool",
    project_urls={
        "Bug Reports": "https://github.com/tongyi-agent/tongyi-agent/issues",
        "Source": "https://github.com/tongyi-agent/tongyi-agent",
        "Documentation": "https://github.com/tongyi-agent/tongyi-agent#readme",
    },
)