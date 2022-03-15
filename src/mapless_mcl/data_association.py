from typing import List

from shapely.geometry import Point

from mapless_mcl.trajectory import Trajectory
from mapless_mcl.hlmap import HLMap
import numpy as np

def associate_observed_speed_limit(
    speedlimit : int, trajectory : Trajectory, hlmap : HLMap
) -> List[int]:
    """Retrieves the trajectory sequence ids that have the observed speed limit property."""
    osm_ids = trajectory.get_reference_osm_ids()
    road_elements = hlmap.get_by_osm_ids(osm_ids)
    matched_elements = road_elements[road_elements.maxspeed == speedlimit]
    # Which are the indices from the osm_ids that are contained in the matched elements?
    ids = []
    for i, osm_id in enumerate(osm_ids):
        if np.any(matched_elements.osm_id == osm_id):
            ids.append(i)
    return ids

def associate_found_intersection_evidence(
    trajectory : Trajectory, hlmap : HLMap
) -> List[float]:
    """Observed a stop sign or traffic light, which means that there must be an intersection 
    nearby.
    
    Retrieves the list of offsets in the trajectory in which roads intersect.
    """
    roadmap_linestrings = hlmap.get_roadmap_linestrings()
    offsets = []

    for seq_id, line in enumerate( trajectory.get_linestrings() ):

        # The street where the current trajectory element is referenced
        sequence_element_row = trajectory.at_sequence_id(seq_id)
        ref_osm_id = sequence_element_row["ref_osm_id"]
        reference_street_linestring = hlmap.get_by_osm_ids([ref_osm_id]).geometry.iloc[0]

        # Get intersection points in the road map
        intersection_indices = roadmap_linestrings.sindex.query(reference_street_linestring, predicate='intersects')
        intersection_series = roadmap_linestrings.iloc[intersection_indices].intersection(reference_street_linestring, align=True,)
        intersection_series = intersection_series[ ~intersection_series.is_empty ]
        
        # Include the intersection points to the ids
        # - Note that the intersection of the reference street with self 
        # returns a LineString geometry, so it is ignored.
        for geometry in intersection_series:

            if isinstance(geometry,Point):
                # Ignores geometries that are too far from the line
                if geometry.distance(line) >= 10.0:
                    continue 
                offset_in_trajectory_linestring = line.project(geometry)

                # Ignores points after the trajectory bounds
                if offset_in_trajectory_linestring >= line.length:
                    continue
                offset_until_trajectory_linestring = trajectory.offset_at_sequence_id(seq_id)
                offsets.append(offset_in_trajectory_linestring + offset_until_trajectory_linestring)
                
    return offsets

def associate_observed_one_way_sign( trajectory : Trajectory, hlmap : HLMap ) -> List[float]:
    """Observed a one-way sign, which 

    Retrieves the list of offsets in the trajectory in which the road that 
    intersects is one-way.
    """
    pass