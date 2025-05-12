from setuptools import find_packages, setup

# Read the contents of the README file
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

# Import the version from the package
from src.minimalagent import __version__

setup(
    name="minimalagent",
    version=__version__,
    description="A lightweight agent framework for Amazon Bedrock",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Nikhil Palmar",
    author_email="nipalm@amazon.com",
    url="https://github.com/nipalm/minimalagent",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "boto3>=1.38.13",
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
