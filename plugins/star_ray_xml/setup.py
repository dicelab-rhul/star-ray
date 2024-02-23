from setuptools import setup, find_namespace_packages

setup(
    name="star_ray_xml",
    packages=find_namespace_packages(include=["star_ray.plugin.xml"]),
)
