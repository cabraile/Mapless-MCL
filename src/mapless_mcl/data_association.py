from typing import List

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

def associate_stop_signs(trajectory : Trajectory, hlmap : HLMap) -> List[float]:
    """Observed a stop sign, which means that there must be an intersection 
    nearby.
    
    Retrieves the list of offsets in the trajectory in which roads intersect.
    """
    pass


def associate_observed_one_way_sign( trajectory : Trajectory, hlmap : HLMap ) -> List[float]:
    """Observed a one-way sign, which 

    Retrieves the list of offsets in the trajectory in which the road that 
    intersects is one-way.
    """
    pass