import os
import argparse
import numpy as np
import geopandas as gpd
from mapless_mcl.hlmap import HLMap
from mapless_mcl.trajectory import Trajectory
from mapless_mcl.drmcl import DRMCL

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--road_map", required=True,  help="")
    parser.add_argument("--trajectory", required=True, help="")
    parser.add_argument("--export_dir", required=True, help="")
    parser.add_argument("--n_particles", required=False, type=int, default=100, help="")
    return parser.parse_args()

def main() -> int:
    args = parse_args()
    # Load the map elements
    hlmap = HLMap()
    hlmap.load(os.path.abspath(args.road_map))
    trajectory = Trajectory(os.path.abspath(args.trajectory))

    # Apply the filter's prediction
    mcl = DRMCL()
    mcl.sample( args.n_particles, trajectory.id )
    outcomes = []
    for t in range(400):
        default_control = np.array([10.0, 5.0, 0.0]) # x, y, yaw
        default_covariance = np.diag([0.01, 0.01, 0.001])
        mcl.predict(default_control, default_covariance)
        centroids, covariances = mcl.get_position(trajectories=[trajectory])
        centroid = centroids[0]
        covariance = covariances[0]
        results = {"timestamp" : t, "geometry" : centroid}
        outcomes.append(results)

    # Store to disk
    export_dir = os.path.abspath(args.export_dir)
    outcomes_gdf = gpd.GeoDataFrame(outcomes, crs=hlmap.get_crs()).to_crs("EPSG:4326")
    outcomes_gdf.to_file(os.path.join(export_dir, "outcomes.geojson"), driver="GeoJSON")

    return 0

if __name__ == "__main__":
    exit(main())