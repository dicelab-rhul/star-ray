from setuptools import setup, find_packages

setup(
    name="star_ray_example_vacuumworld",
    version="0.0.1",
    author="Benedict Wilkins",
    author_email="benrjw@gmail.com",
    description="",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["star_ray"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
