from setuptools import setup, find_packages

# python setup.py sdist     # Creates a new archive in dist
setup(
    name="thingsboard_api_tools",
    version="0.2",
    description="Tools for interacting with the Thingsboard API",
    url="https://github.com/eykamp/thingsboard_api_tools",
    author="Chris Eykamp",
    author_email="chris@eykamp.com",
    license="MIT",
    packages=find_packages(),  # Automatically find all packages and sub-packages
    zip_safe=False,
    python_requires='>=3.10',
    install_requires=[
        "requests",  # Add other dependencies here
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
