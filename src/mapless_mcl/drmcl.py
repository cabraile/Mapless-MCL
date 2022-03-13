from typing import List, Tuple

import numpy as np

from shapely.geometry import Point

from mapless_mcl.trajectory import Trajectory

class DRMCL:
    """Distance-Route-based Monte Carlo Localization."""

    def __init__(self) -> None:
        self.offsets = None
        pass

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

    def update(self) -> None:
        pass
