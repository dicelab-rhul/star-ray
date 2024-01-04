from setuptools import setup, find_packages

setup(
    name="icua2",
    version="2.0.1",
    author="Benedict Wilkins",
    author_email="benrjw@@gmail.com",
    description="",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "svgrenderengine>=0.1.0",
        "blinker>=1.7.0",  # event system
    ],
    extras_require={
        "eyetracking": [],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
