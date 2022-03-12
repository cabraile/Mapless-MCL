from typing import Any, Tuple
import numpy as np
import scipy.stats

def low_variance_sampler(weights : np.ndarray) -> np.ndarray:
  """Samples ids proportional to the weights provided.

  Parameters
  ------------
  weights:
      The weights of the particles. Will be normalized in this function.

  Returns
  ------------
  The new ids for sampling the particles with replacement proportional to their 
  weights.
  """
  sum_w = np.sum(weights)
  if(sum_w == 0):
      return np.arange(0, weights.size)
  w = weights / sum_w
  n_particles = w.size
  delta = 1./n_particles
  r_init = np.random.rand() * delta
  ids = np.zeros((n_particles),dtype=int)
  
  i = 0
  cumulative_w = w[0]
  for k in range(n_particles):
    # The next cumulative weight has to be greater than this
    r = r_init + k * delta
    while r > cumulative_w:
      # Increment the cumulative weight: still not enough
      i += 1
      cumulative_w += w[i]
    ids[k] = i
    
  return ids

def maximum_likelihood_estimation(poses : np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
  """Estimate the mean and covariance of the normal distribution that best fits 
  the data.
  """
  mean_position = np.average(poses[:,:2],axis=0).flatten()
  mean_orientation = scipy.stats.circmean(poses[:,2], low=-np.pi, high=np.pi)
  position_covariance = np.cov(poses[:,:2].T)
  orientation_variance = scipy.stats.circvar(poses[:,2])
  mean = np.hstack([mean_position, mean_orientation])
  covariance = np.zeros((3,3))
  covariance[:2,:2] = position_covariance
  covariance[2,2] = orientation_variance
  return mean, covariance