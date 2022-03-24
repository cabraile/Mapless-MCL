from setuptools import setup

setup(
    name="Mapless MCL",
    description="Mapless Monte-Carlo Localization implementation approaches",
    package_dir={"" : "src"},
    packages=["mapless_mcl", "mapless_demos"],
    install_requires = ["numpy>=1.18.5", "shapely", "pyproj", "rtree", "geopandas", "utm", "scipy", "matplotlib", "python-dateutil>=2.8.1"]
)