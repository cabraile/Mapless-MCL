from setuptools import setup

setup(
    name="Mapless MCL",
    description="Mapless Monte-Carlo Localization implementation approaches",
    package_dir={"" : "src"},
    packages=["mapless_mcl", "mapless_demos"],
    install_requires = ["numpy", "shapely", "pyproj", "geopandas", "utm", "scipy", "matplotlib"]
)