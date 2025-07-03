from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="streetwear-inventory-cli",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.0.0",
        "sqlalchemy>=2.0.0",
        "pyyaml>=6.0.0",
        "pillow>=9.0.0",
    ],
    extras_require={
        "api": ["flask>=2.3.0", "flask-cors>=4.0.0"],
        "excel": ["pandas>=1.5.0", "openpyxl>=3.1.0"],
        "dev": ["pytest>=7.0.0", "pytest-cov>=4.0.0"],
        "all": ["flask>=2.3.0", "flask-cors>=4.0.0", "pandas>=1.5.0", "openpyxl>=3.1.0"],
    },
    entry_points={
        "console_scripts": [
            "inv=inv.cli:main",
        ],
    },
    author="Streetwear Inventory CLI",
    author_email="",
    description="Professional-grade inventory management system for streetwear resellers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/streetwear-inventory-cli",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/streetwear-inventory-cli/issues",
        "Source": "https://github.com/yourusername/streetwear-inventory-cli",
        "Documentation": "https://github.com/yourusername/streetwear-inventory-cli#readme",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Point-Of-Sale",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
    ],
    keywords="streetwear inventory management cli sneakers reselling consignment",
    python_requires=">=3.8",
    zip_safe=False,
)
