from typing import List, Tuple

import numpy as np

from shapely.geometry import Point

from mapless_mcl.mcl import low_variance_sampler
from mapless_mcl.hlmap import HLMap
from mapless_mcl.trajectory import Trajectory
from mapless_mcl.data_association import associate_observed_speed_limit

class DRMCL:
    """Distance-Route-based Monte Carlo Localization."""

    def __init__(self) -> None:
        self.offsets = None

    # Data flow
    # =========================================================================

    def assign_map(self, hlmap : HLMap) -> None:
        self.hlmap = hlmap

    def get_particles(self, trajectories : List[Trajectory ]) -> Tuple[List[Point]]:
        """Returns the particles in the XY plane"""
        points = []
        for trajectory in trajectories:
            # Retrieve the particles that belong to the given trajectory
            offsets = self.offsets[ np.where( self.trajectories == trajectory.id ) ]

            # Compute the position of each particle in the trajectory
            points += [ trajectory.at_offset(offset) for offset in offsets ]

        return points

    def get_position(self, trajectories : List[Trajectory]) -> Tuple[List[Point], List[np.ndarray]]:
        """Returns the estimated position and covariance for each trajectory provided."""
        centroids = []
        covariance_matrices = []
        for trajectory in trajectories:
            # Retrieve the particles that belong to the given trajectory
            offsets = self.offsets[ np.where( self.trajectories == trajectory.id ) ]

            # Compute the position of each particle in the trajectory
            points = [ trajectory.at_offset(offset) for offset in offsets ]
            points_array = np.array( [ tuple(p.coords)[0] for p in points] )

            # Compute the centroid of the projected particles
            centroid_array = np.mean(points_array, axis=0)
            centroid = Point(*centroid_array[:2])

            # Estimate their covariance
            covariance_matrix = np.cov(points_array.T)

            # Store
            centroids.append(centroid)
            covariance_matrices.append(covariance_matrix)
        return centroids, covariance_matrices

    # =========================================================================

    # 
    # =========================================================================

    def sample(self, n_particles : int, trajectory_id : str ) -> None:
        self.offsets = np.zeros((n_particles,1), dtype=float)
        self.trajectories = np.full((n_particles,1), trajectory_id)

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

    def weigh_by_speedlimit(
        self, 
        trajectory : Trajectory,
        detected_speedlimit : int,
        model_sensitivity : float,
        model_false_positive_rate : float,
    ) -> np.ndarray:
        seq_ids = associate_observed_speed_limit(speedlimit=detected_speedlimit,trajectory=trajectory, hlmap = self.hlmap)
        factor = 1./(model_sensitivity + model_false_positive_rate)
        weights = []
        for offset in self.offsets:
            seq_id = trajectory.sequence_at_offset(offset)
            if seq_id in seq_ids:
                w = model_sensitivity * factor # Normalized sensitivity
            else:
                w = model_false_positive_rate * factor # normalized FPR
            weights.append(w)
        return np.array(weights)

    # =========================================================================