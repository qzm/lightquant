from setuptools import setup, find_packages

setup(
    name="lightquant",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy",
        "pandas",
        "numpy",
        "matplotlib",
        "ccxt",
        "python-dateutil",
    ],
    author="LightQuant Team",
    author_email="info@lightquant.org",
    description="A lightweight quantitative trading framework for digital currencies",
    keywords="cryptocurrency, trading, quantitative, backtesting",
    url="https://github.com/lightquant/lightquant",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
) 