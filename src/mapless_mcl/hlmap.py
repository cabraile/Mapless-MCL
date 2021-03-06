import os
from typing import Iterable

import pandas as pd
from shapely.geometry import Point
import geopandas as gpd
import pyproj

from mapless_mcl.geoutils import project_geodataframe_to_best_utm
from mapless_mcl.parsers import tag_as_dict

class HLMap:
    
    def __init__(self) -> None:
        self.roadmap_layer = None

    def load(self, path : os.PathLike) -> None:
        """Loads the linestrings of the map."""
        gdf = gpd.read_file(path).to_crs("EPSG:4326")
        gdf, utm_crs = project_geodataframe_to_best_utm(gdf)
        
        # Split the "other_tags" to new columns
        other_tags_dataframe = gdf.other_tags.apply( lambda tag : pd.Series(tag_as_dict(tag), dtype=object) )
        
        # Store
        self.crs = utm_crs
        self.roadmap_layer = gpd.GeoDataFrame(pd.concat([gdf,other_tags_dataframe],axis="columns")).drop(columns=["other_tags"]).set_index("osm_id")

    def get_by_osm_ids(self, ids : Iterable ) -> gpd.GeoDataFrame:
        return self.roadmap_layer.loc[ids]

    def geometry(self) -> gpd.GeoSeries:
        return self.roadmap_layer.geometry

    def get_roadmap_linestrings(self) -> gpd.GeoSeries:
        return self.roadmap_layer.geometry

    def get_origin(self,) -> Point:
        """Computes the extreme minimum coordinates of the map."""
        bounds = self.roadmap_layer.total_bounds
        min_x, min_y = bounds[:2]
        return Point(min_x, min_y)

    def get_crs(self) -> pyproj.CRS:
        return self.crs

    def __getitem__(self, ids : Iterable):
        return self.roadmap_layer.loc[ids]