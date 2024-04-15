from setuptools import setup, find_namespace_packages

setup(
    name="star_ray_xml",
    version="0.0.1",
    author="Benedict Wilkins",
    author_email="benrjw@gmail.com",
    description="",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_namespace_packages(
        include=["star_ray.plugin.xml", "star_ray.plugin.xml.*"]
    ),
    include_package_data=True,
    python_requires=">=3.10",
)
