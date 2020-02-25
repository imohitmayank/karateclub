import numpy as np
import networkx as nx
import scipy.sparse as sps
from karateclub.estimator import Estimator

class NetLSD(Estimator):
    r"""An implementation of `"NetLSD" <https://arxiv.org/abs/1805.10712>`_
    from the KDD '18 paper "NetLSD: Hearing the Shape of a Graph". The procedure
    calculate the heat kernel trace of the normalized Laplacian matrix over a
    vector of time scales. If the matrix is large it switches to an approximation
    of the eigenvalues. 

    Args:
        scale_min (int): Time scale interval minimum. Default is -2.0.
        scale_max (int): Time scale interval maximum. Default is 2.0.
        scale_steps (int): Number of steps in time scale. Default is 250.
        scale_approximations (int): Number of eigenvalue approximations. Default is 50.
    """
    def __init__(self, scale_min = -2.0, scale_max=2.0, scale_steps=250, approximations=50):
        self.scale_min = scale_min
        self.scale_max = scale_max
        self.scale_steps = scale_steps
        self.approximations = approximations
   
    def _calculate_heat_kernel_trace(self, eivals):
        timescales = np.logspace(self.scale_min, self.scale_max, self.scale_steps)
        nodes = eivals.shape[0]
        heat_kernel_trace = np.zeros(timescales.shape)
        for idx, t in enumerate(timescales):
            heat_kernel_trace[idx] = np.sum(np.exp(-t * eivals))
        heat_kernel_trace = heat_kernel_trace / nodes
        return heat_kernel_trace

    def _updown_linear_approx(self, eigvals_lower, eigvals_upper, nv):
        nal = len(eigvals_lower)
        nau = len(eigvals_upper)
        ret = np.zeros(nv)
        ret[:nal] = eigvals_lower
        ret[-nau:] = eigvals_upper
        ret[nal-1:-nau+1] = np.linspace(eigvals_lower[-1], eigvals_upper[0], nv-nal-nau+2)
        return ret

    def _calculate_eigenvalues(self, mat):
        nv = mat.shape[0]
        if 2*self.approximations + 2< nv:
            lo_eivals = sps.linalg.eigsh(mat, self.approximations, which="SM", return_eigenvectors=False, mode="cayley")[::-1]
            up_eivals = sps.linalg.eigsh(mat, self.approximations, which="LM", return_eigenvectors=False, mode="cayley")
            return self._updown_linear_approx(lo_eivals, up_eivals, nv)
        else:
            return sps.linalg.eigsh(mat, nv-1, which="SM", return_eigenvectors=False)


    def _calculate_netlsd(self, graph):
        """
        Calculating the features of a graph.

        Arg types:
            * **graph** *(NetworkX graph)* - A graph to be embedded.

        Return types:
            * **hist** *(Numpy array)* - The embedding of a single graph.
        """
        graph.remove_edges_from(nx.selfloop_edges(graph))
        normalized_laplacian = sps.coo_matrix(nx.normalized_laplacian_matrix(graph, nodelist = range(graph.number_of_nodes())))
        eigen_values = self._calculate_eigenvalues(normalized_laplacian)
        heat_kernel_trace = self._calculate_heat_kernel_trace(eigen_values)
        return heat_kernel_trace

    def fit(self, graphs):
        """
        Fitting a NetLSD model.

        Arg types:
            * **graphs** *(List of NetworkX graphs)* - The graphs to be embedded.
        """
        self._embedding = [self._calculate_netlsd(graph) for graph in graphs]


    def get_embedding(self):
        r"""Getting the embedding of graphs.

        Return types:
            * **embedding** *(Numpy array)* - The embedding of graphs.
        """
        return np.array(self._embedding)
