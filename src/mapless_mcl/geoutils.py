from typing import Tuple
from pyproj import CRS
import geopandas as gpd
import utm

def get_utm_crs_from_lat_lon( latitude : float, longitude : float ) -> CRS:
    _,_, zone_number, zone_letter = utm.from_latlon(latitude, longitude)
    hemisphere = "north" if zone_letter.upper() >= "N" else "south"
    crs = CRS.from_string(f"+proj=utm +zone={zone_number} +{hemisphere}")
    return crs

def project_geodataframe_to_best_utm(gdf : gpd.GeoDataFrame) -> Tuple[gpd.GeoDataFrame, CRS]:
    # Find the centroid of the bounds
    bounds = gdf.bounds
    centroid_longitude = ( (bounds["minx"] + bounds["maxx"])/2 ).iloc[0]
    centroid_latitude = ( (bounds["miny"] + bounds["maxy"])/2 ).iloc[0]
    # Get projection
    utm_crs = get_utm_crs_from_lat_lon(centroid_latitude, centroid_longitude)
    # Project and return
    return gdf.to_crs(utm_crs), utm_crs