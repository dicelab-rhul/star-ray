from setuptools import setup, find_packages

setup(
    name="star_ray_web",
    version="0.0.1",
    author="Benedict Wilkins",
    author_email="benrjw@gmail.com",
    description="",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "ray[serve]==2.9.1",
        "starlette<=0.34.0",  # this version is required to prevent an error in ray serve (it should be fixed in ray 2.10)
    ],
    package_data={
        "": ["*.js"],
        "star_ray_web": [
            "static/js/*.js",
            "static/js/*.js.jinja",
            "static/svg/*.svg",
            "static/svg/*.svg.jinja",
            "static/templates/*.html",
            "static/templates/*.html.jinja",
        ],
    },
    include_package_data=True,
    python_requires=">=3.10",
)
