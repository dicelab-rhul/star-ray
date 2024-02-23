from setuptools import setup, find_packages

setup(
    name="star_ray",
    version="2.0.1",
    author="Benedict Wilkins",
    author_email="benrjw@gmail.com",
    description="",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "ray[serve]==2.9.1",
        "starlette<=0.34.0",  # this version is required to prevent an error in ray serve (it should be fixed in ray 2.10)
        "uuid",
        "cairosvg",
        "jinja2",
        "lxml",
        "numpy",
        "numexpr",
        "omegaconf",
        "h5py",
        # "pylint",
    ],
    extras_require={
        # "web": ["./plugins/web"], # TODO the relative path doesnt seem to work...
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
