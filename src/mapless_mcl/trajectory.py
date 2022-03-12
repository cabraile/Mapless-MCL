import os
from itertools import count
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from mapless_mcl.geoutils import project_geodataframe_to_best_utm

class Trajectory:
    """"""
    __INSTANCE_COUNT__ = count(0)
    def __init__(self, path : os.PathLike):
        """
        Arguments
        --------
        path:
            The path to the virtual trajectory's file stored as a collection of
            LineString geometries.
        """
        self.id = f"{next(Trajectory.__INSTANCE_COUNT__):06}"
        trajectory = gpd.GeoDataFrame.from_file(path).sort_values(by="seq_id")
        
        # Project to metric coordinates
        trajectory, crs = project_geodataframe_to_best_utm(trajectory)
        
        # Fill the cumulative offset
        trajectory["cumulative_offset"] = np.cumsum( [ line.length for line in trajectory.geometry ] )

        self.trajectory = trajectory

    def at_offset(self, offset : float) -> Point:
        """Given an offset in meters, returns the coordinates at the given 
        position.
        
        TODO: in case of negative offset or offset > total_length, the 
        interpolated points are generated in the borders, not beyond them.
        """
        ids = np.where( offset < self.trajectory.cumulative_offset )[0]

        # Get the position before the first occurrence of the offset being 
        # greater than the cumulative offset
        if len(ids) != 0:
            idx = ids[0]

        # If the offset is greater than the total cumulative offset, then 
        # retrieve the last trajectory element
        else:
            idx = -1

        # If idx is 0, it means that there is no cumulative offset before
        # this offset.
        if idx == 0:
            cumulative_offset = 0 
        # If idx is -1, means that the offset is greater than the total offset
        # of the trajectory
        elif idx == -1:
            cumulative_offset = self.trajectory.iloc[-1].cumulative_offset
        # Otherwise, retrieves the accumulated offset so far
        else:
            cumulative_offset = self.trajectory.iloc[idx - 1].cumulative_offset

        # Computes the displacement inside the selected trajectory element
        relative_offset = offset - cumulative_offset

        # Projects to the world coordinates
        trajectory_element = self.trajectory.iloc[idx]
        position = trajectory_element.geometry.interpolate(relative_offset)
        return position
