from setuptools import setup, find_namespace_packages

setup(
    name="star_ray_web",
    version="0.0.1",
    author="Benedict Wilkins",
    author_email="benrjw@gmail.com",
    description="",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_namespace_packages(include=["star_ray.plugin.web"]),
    install_requires=[
        "ray[serve]==2.9.1",
        "starlette<=0.34.0",  # this version is required to prevent an error in ray serve (it should be fixed in ray 2.10)
    ],
    package_data={
        "star_ray.plugin.web": [
            "static/*",
        ],
    },
    include_package_data=True,
    python_requires=">=3.10",
)
