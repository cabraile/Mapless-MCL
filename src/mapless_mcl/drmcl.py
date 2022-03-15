from typing import List, Tuple

import numpy as np

from shapely.geometry import Point

from mapless_mcl.mcl import low_variance_sampler
from mapless_mcl.hlmap import HLMap
from mapless_mcl.trajectory import Trajectory
from mapless_mcl.data_association import associate_found_intersection_evidence, associate_observed_speed_limit

class DRMCL:
    """Distance-Route-based Monte Carlo Localization."""

    def __init__(self) -> None:
        self.offsets = None
        self.hlmap = None
        self.trajectory = None
        self.features = {
            "intersections" : {}
        }

    # Data flow
    # =========================================================================

    def assign_map(self, hlmap : HLMap) -> None:
        self.hlmap = hlmap

    def assign_trajectory(self, trajectory : Trajectory) -> None:
        self.trajectory = trajectory

    def load_trajectory_intersections(self) -> None:
        # TODO: refactor the function... feels weird
        self.features["intersections"] = associate_found_intersection_evidence(self.trajectory, self.hlmap)

    def get_particles(self) -> List[Point]:
        """Returns the particles in the XY plane"""
        points = []

        # Compute the position of each particle in the trajectory
        points = [ self.trajectory.at_offset(offset) for offset in self.offsets.flatten() ]

        return points

    def get_position(self) -> Tuple[Point, np.ndarray]:
        """Returns the estimated position and covariance for each trajectory provided."""

        # Compute the position of each particle in the trajectory
        points = [ self.trajectory.at_offset(offset) for offset in self.offsets.flatten() ]
        points_array = np.array( [ tuple(p.coords)[0] for p in points] )

        # Compute the centroid of the projected particles
        centroid_array = np.mean(points_array, axis=0)
        centroid = Point(*centroid_array[:2])

        # Estimate their covariance
        covariance_matrix = np.cov(points_array.T)
        
        # "artificial fill" TODO: make it correct! In theory, handle perpendicular lines of the lanes
        value = max(np.max(covariance_matrix), 4.0 ) 
        covariance_matrix = np.diag( [value, value] )

        # Store
        
        return centroid, covariance_matrix

    # =========================================================================

    # 
    # =========================================================================

    def sample(self, n_particles : int) -> None:
        self.offsets = np.zeros((n_particles,1), dtype=float)

    def predict(self, control_array : np.ndarray, covariance : np.ndarray) -> None:
        """Performs state prediction based on the control commands given and the 
        covariance matrix.
        """
        u = control_array.flatten()
        noise_array = np.random.multivariate_normal( mean=np.zeros_like(u), cov=covariance , size=len(self.offsets))
        displacement = np.array( [ [np.linalg.norm(u)] ] * self.offsets.shape[0] )
        self.offsets = self.offsets + displacement + noise_array[:,0].reshape(-1,1)

    def resample(self, weights : np.ndarray) -> None:
        ids = low_variance_sampler(weights)
        self.offsets = self.offsets[ids]

    # =========================================================================

    # Update-related
    # =========================================================================

    def weigh_by_speed_limit(
        self, 
        detected_speed_limit : int,
        model_sensitivity : float,
        model_false_positive_rate : float,
    ) -> np.ndarray:
        # Get the 
        seq_ids = associate_observed_speed_limit( speedlimit=detected_speed_limit, trajectory=self.trajectory, hlmap = self.hlmap)
        factor = 1./(model_sensitivity + model_false_positive_rate)
        weights = []
        for offset in self.offsets:
            seq_id = self.trajectory.sequence_id_at_offset(offset)
            if seq_id in seq_ids:
                w = model_sensitivity * factor # Normalized sensitivity
            else:
                w = model_false_positive_rate * factor # normalized FPR
            weights.append(w)
        return np.array(weights)

    def weigh_by_intersection_evidence( self,
        detection_label : str,
        model_sensitivity : float,
        model_false_positive_rate : float,
    ) -> np.ndarray:
        if detection_label == "stop sign":
            default_detection_min_distance = 0.5 # Minimum distance from intersection for expecting detection
            default_detection_max_distance = 2.0 # Maximum distance from intersection for expecting detection
        else:
            default_detection_min_distance = 1.0 # Minimum distance from intersection for expecting detection
            default_detection_max_distance = 15.0 # Maximum distance from intersection for expecting detection

        intersections_at_offsets = self.features["intersections"]
        
        # Find which particles belong to the intersection range and which don't
        mask = np.full_like( self.offsets, False, dtype=bool )
        for offset in intersections_at_offsets:
            range_max = offset - default_detection_min_distance # The max offset the particle can have to be inside the detection zone
            range_min = offset - default_detection_max_distance # The min offset the particle can have to be inside the detection zone
            # Mask of particles that belong to the detection zone
            mask = mask | (  (self.offsets > range_min ) & (self.offsets < range_max ) )

        factor = 1./(model_sensitivity + model_false_positive_rate)
        normalized_sensitivity = model_sensitivity * factor
        normalized_fpr = model_false_positive_rate * factor
        
        # All particles that are inside the detection zone are marked with the 
        # normalized sensitivity rate; the other are marked with the normalized
        # False Positive Rate
        weights = np.full_like(self.offsets, fill_value = normalized_fpr)
        weights[np.where(mask)] = normalized_sensitivity

        return weights

    # =========================================================================