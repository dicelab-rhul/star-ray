from setuptools import setup, find_packages

setup(
    name="star_ray",
    version="0.0.3",
    author="Benedict Wilkins",
    author_email="benrjw@gmail.com",
    description="A multi-agent simulation platform based on the distributed computing platform `ray`.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    url="https://github.com/dicelab-rhul/star-ray",
    install_requires=[
        "ray>=2.9.1",
        "starlette<=0.34.0",
        "jinja2",
        "starlette",
        "pydantic",
        "deepmerge",
        "cerberus",
    ],
    extras_require={
        "xml": ["star_ray_xml"],
        "pygame": ["star_ray_pygame"],
        # "web" : ["star_ray_web"] # not currently available...
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.10",
    ],
)
