from setuptools import setup, find_packages

setup(
    name="agent_module",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'flask',
        'flask-login',
    ],
    author="ProEthica Team",
    author_email="info@proethica.org",
    description="A modular agent implementation for conversational AI interfaces",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
