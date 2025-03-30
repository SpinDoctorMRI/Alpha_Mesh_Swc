import numpy as np
import warnings
from numpy.linalg import norm
import pymeshlab as mlab
from .tendril import Tendril
import os
from .mesh_processing import simplify_mesh, dcp_meshset
import time
import sys
from .segments import Sphere, Frustum, Segment
from multiprocessing import Pool
from copy import deepcopy as dcp


class Swc:
    """Class to store and process nodes from swc data. This class stores the skeleton information we get from the swc files
    attributes:
        file
        position_data
        radius_data
        conn_data
        type_data
        premable: (string) text from beginning of swc file
        process: (bool) flag to denote whether to process swc
        Delta: (processing parameter) target average distance between nodes
        delta: (proccessing parameter) target average distance between nodes close to the soma
        branches: (array) stores the branch to which each node belongs.
        intersection_matrix: (sparse matrix) stores cross-branch intersections of nodes

    methods:
        write: write new processed data in swc format
        initialise_branches: finds branches of swc file.
        make_mesh: produce watertight surface mesh and save


    """

    def __init__(self, file=None, process=False, reorder=True, Delta=2.0, delta=1.0):

        # Store separate timings of all steps.
        self.timings = dict()
        start = time.time()

        # Read file
        self.file = os.path.abspath(file)
        position_data, radius_data, conn_data, type_data, preamble = extract_swc(
            self.file
        )
        self.timings["extract_swc"] = time.time() - start

        # Check for correct ordering
        start = time.time()
        if reorder:
            if not (
                conn_data[0, 1] == -1 and np.all(conn_data[1:, 0] > conn_data[1:, 1])
            ):
                print("Reordering swc")
                position_data, radius_data, conn_data, type_data = reorder_swc(
                    position_data, radius_data, conn_data, type_data
                )
            self.timings["reorder_swc"] = time.time() - start

        # Apply Swc processing
        if process:
            start = time.time()
            if not (reorder):
                msg = f"Must reorder swc file {file} before processing."
                warnings.warn(msg, RuntimeWarning, stacklevel=2)
                position_data, radius_data, conn_data, type_data = reorder_swc(
                    position_data, radius_data, conn_data, type_data
                )

            position_data, radius_data, conn_data, type_data = smooth_swc(
                position_data, radius_data, conn_data, type_data, Delta
            )
            position_data, radius_data, conn_data, type_data = interpolate_swc(
                position_data, radius_data, conn_data, type_data, delta
            )
            self.timings["process_swc"] = time.time() - start

        # Store data
        self.position_data = position_data
        self.radius_data = radius_data
        self.type_data = type_data
        self.conn_data = conn_data
        self.process = process
        self.preamble = preamble

        # Compute branches
        start = time.time()
        self.initialise_branches()
        self.timings["initialise_branches"] = time.time() - start
        self.Delta = Delta

        return None

    def write(self, append_clean=True):
        """Write the processed swc file in swc format"""
        if append_clean:
            file = self.file.replace(".swc", "_clean.swc")
        data = []
        N = len(self.position_data)
        conn_data = np.copy(self.conn_data)
        source_nodes = conn_data[:, 1] == -1
        conn_data[:, 0] = conn_data[:, 0] + 1
        conn_data[~source_nodes, 1] = conn_data[~source_nodes, 1] + 1
        for i in range(0, N):
            entry = "{0} {1} {2} {3} {4} {5} {6} \n".format(
                int(conn_data[i, 0]),
                int(self.type_data[i]),
                self.position_data[i, 0],
                self.position_data[i, 1],
                self.position_data[i, 2],
                self.radius_data[i],
                int(conn_data[i, 1]),
            )
            data.append(entry)
        with open(file, "w") as f:
            f.writelines(self.preamble)
            f.writelines(data)
        return file

    def initialise_branches(self):
        """Creates branches along the neuron"""
        self.branches = create_branches(self.conn_data, self.type_data)
        return None

    def _build_initial_mesh(self, merge=True):
        """Produce the inital non-watertight mesh by placing spheres at somas and junctions and tubular meshes along branches"""

        # Create meshset to store all meshes
        ms = mlab.MeshSet()

        # Create sphere to translate and scale
        ms.create_sphere(radius=1)
        v_S = ms.current_mesh().vertex_matrix()
        f_S = ms.current_mesh().face_matrix()
        ms.clear()

        # extract data
        b = self.branches
        p = self.position_data
        r = self.radius_data
        t = self.type_data
        c = self.conn_data
        N = len(r)

        start = time.time()
        # Place spheres at somas
        for i in range(0, N):
            if t[i] == 1:
                m = mlab.Mesh(vertex_matrix=p[i] + r[i] * v_S, face_matrix=f_S)
                ms.add_mesh(m)

        # Produce tubular meshes along branches
        branch_ids = np.unique(b)
        for branch in branch_ids:
            if branch > 0:
                # Get relevent nodes for this branch
                nodes = np.where(b == branch)[0]
                nodes = np.hstack((c[nodes[0], 1], nodes))
                n = np.where(c[:, 1] == nodes[-1])[0]
                if len(n) > 0:
                    nodes = np.hstack((nodes, n[0]))
                # Create tubular mesh
                tendril = Tendril(nodes, self, 0)
                v, f = tendril.make_mesh(v_S, f_S)
                # Store mesh
                m = mlab.Mesh(vertex_matrix=v, face_matrix=f)
                ms.add_mesh(m)

        self.timings["initialising_individual_meshes"] = time.time() - start

        # Merge individual meshes
        if merge:
            start = time.time()
            print(f"merging {ms.mesh_number()} meshes")
            ms.generate_by_merging_visible_meshes()
            self.timings["merging_individual_meshes"] = time.time() - start
        return ms

    def _simplify_mesh(
        self, ms_alpha, min_faces, dfaces, temp_dir_name, min_r_min=0.05
    ):
        """Calls simplfication proceedure on ms_alpha. Simplfication parameters comes from Swc and min_faces,dfaces"""
        start = time.time()

        # Get length of Swc file
        total_length = self.get_length()

        # Create dfaces
        if dfaces is None:
            dfaces = int(total_length * 8)
        if min_faces is None or int(min_faces) < dfaces / 2:
            min_faces = int(total_length * 2)

        print(f"Simplifying {self.file} to at least {min_faces} faces")

        # Extract minimum radius of the Swc file
        r_min = max(min(self.radius_data), min_r_min)

        # Call mesh simplification proceedure
        ms = simplify_mesh(ms_alpha, dfaces, r_min, min_faces, temp_dir_name)

        # Record timings
        self.timings["simplify_mesh"] = time.time() - start

        return ms

    def make_mesh(
        self,
        simplify=False,
        alpha_fraction=None,
        output_dir=None,
        save=True,
        min_faces=None,
        dfaces=None,
        save_alpha_mesh=False,
    ):
        """Compute watertight surface mesh
        Args:
            self: swc object
            simplify: (bool) flag to simplify after alpha wrapping stage
            alpha_fraction: (float) postive parameter of alpha wrapping stage.
                Default depends on the ratio of the minimum cross-sectional radius and the diagonal of a bounding box.
            output_dir: (string) directory to save the mesh into. Defaults to same location as swc file.
            save: (bool) flag to save the mesh. Defaults to true.
            min_faces: (int) flag to indicate minimum possible number of faces. Defaults to a computed value depending on the length of the cell.

        Returns:
            ms: (MeshSet) watertight surface mesh of the cell.
            name: (String) namae of saved watertight mesh
            ms_alpha: (MeshSet) watertight surface mesh of the cell from alpha wrapping stage.

        """
        # Store output information
        if output_dir is None:
            name = self.file.replace(".swc", ".ply")
        else:
            filename = os.path.basename(self.file)
            name = output_dir + "/" + filename.replace(".swc", ".ply")

        # Get value for alpha_fraction
        if alpha_fraction is None:
            diag = get_bbox_diag(self.position_data)
            alpha_fraction = max(2 * min(self.radius_data) / diag, 5e-4)

        # Compute individual meshes
        ms = self._build_initial_mesh()

        # Apply alpha_wrap filter
        start = time.time()
        print(f"Applying alpha wrap to {self.file} with alpha = {alpha_fraction}")
        ms.generate_alpha_wrap(
            alpha_fraction=alpha_fraction, offset_fraction=alpha_fraction / 30
        )
        self.timings["alpha_wrap"] = time.time() - start
        ms_alpha = dcp_meshset(ms)
        if save_alpha_mesh:
            ms.save_current_mesh(name.replace(".ply", "_alpha.ply"), binary=False)
        # Begin simplification
        if simplify:
            ms = self._simplify_mesh(ms, min_faces, dfaces, os.path.splitext(name)[0])
        # Save mesh
        if save:
            ms.save_current_mesh(name, binary=False)
        return ms, name, ms_alpha

    def get_length(self):
        """Returns the total length of the swc file"""
        # Extract length of edges between nodes
        edges = np.linalg.norm(
            self.position_data[self.conn_data[self.conn_data[:, 1] > -1, 0], :]
            - self.position_data[self.conn_data[self.conn_data[:, 1] > -1, 1], :],
            axis=1,
        )
        # Extract total sum of edges
        total_length = sum(edges)
        return total_length

    def make_point_cloud(self, density=1.0):
        """Creates a uniform surface point cloud over the swc file"""

        # Create surface point cloud from an Swc file
        print("Creating point cloud")
        segments = []
        N = len(self.type_data)

        # Iterate through segments, appending spheres or Frustrums to list of segments
        for i in range(0, N):
            t = self.type_data[i]
            if t == 1 or self.conn_data[i, 1] == -1:
                node = {}
                node["type"] = t
                node["position"] = self.position_data[i]
                node["radius"] = self.radius_data[i]
                segments.append(Sphere(node, density))
            else:
                end = {}
                end["type"] = t
                end["position"] = self.position_data[i]
                end["radius"] = self.radius_data[i]
                j = self.conn_data[i, 1]
                start = {}
                start["type"] = self.type_data[j]
                start["position"] = self.position_data[j]
                start["radius"] = self.radius_data[j]
                segments.append(Frustum(start, end, density))

        # Remove all interior points from the segments
        self._check_all_intersect(segments)

        # Begin collecting point cloud
        point_list = []
        normal_list = []
        color_list = []
        r_min = np.inf

        # Iterate through segments, extracting points
        for iseg in segments:
            p, n, c = iseg.output()
            point_list.append(p)
            normal_list.append(n)
            color_list.append(c)
            if isinstance(iseg, Frustum):
                r_min = min(r_min, iseg.r_min)
            elif isinstance(iseg, Sphere):
                r_min = min(r_min, iseg.r)

        # Concatenate all points
        points = np.concatenate(point_list, axis=1)
        normals = np.concatenate(normal_list, axis=1)
        colors = np.concatenate(color_list, axis=1)

        # Store point cloud in a mesh
        m = mlab.Mesh(
            vertex_matrix=points.T, v_normals_matrix=normals.T, v_color_matrix=colors.T
        )
        ms = mlab.MeshSet()
        ms.add_mesh(m)

        # Apply some filtering
        ms.meshing_remove_duplicate_vertices()
        bbox = ms.get_geometric_measures()["bbox"]
        ms.meshing_merge_close_vertices(
            threshold=mlab.PercentageValue(10 * r_min / bbox.diagonal())
        )

        # Completed procedure
        print(f"Size of point cloud = {ms.current_mesh().vertex_number()}")
        self.seg = segments
        self.pc = ms
        return ms

    def _check_all_intersect(self, seg):
        """Remove interior points of segments"""

        collision_index_pairs = self.aabb(seg)
        for i, j in collision_index_pairs:
            self._parent_child_intersect(seg, i, j, remove_close_points=False)

        return seg

    def add_mesh_to_point_cloud(self, ms, includemesh=True):
        """Adds a mesh to existing surface point cloud over swc.

        Returns point cloud covering surface of union of the point cloud and surface"""

        # Load segments
        seg = self.seg

        # Load points
        points = ms.current_mesh().vertex_matrix().T
        # Create mask of points that will be kept
        keep = np.full(points.shape[1], True)

        # Create empty Segment for soma
        soma = Segment()
        # Load points, normals and mask into soma
        soma.points = points
        ms.compute_normal_per_vertex()
        soma.normals = ms.current_mesh().vertex_normal_matrix().T
        soma.keep = keep

        # Set infinite radius
        soma.r = np.inf

        # Create axis aligned bounding box for soma
        x = {"min": np.min(points[0, :]), "max": np.max(points[0, :])}
        y = {"min": np.min(points[1, :]), "max": np.max(points[1, :])}
        z = {"min": np.min(points[2, :]), "max": np.max(points[2, :])}
        soma_aabb = x, y, z

        # Remove intersections of soma with other segments
        j = len(seg) - 1
        for i, iseg in enumerate(seg):
            aabb_pair = soma_aabb, iseg.aabb
            if _aabb_collision(aabb_pair):
                inner, on, outer, out_near = iseg.intersect(soma)
                soma.update(outer)

        # Load point cloud mesh
        pc = self.pc
        ms.add_mesh(pc.current_mesh())

        # Compute signed distance field of segments to soma
        ms.compute_scalar_by_distance_from_another_mesh_per_vertex(
            measuremesh=1, refmesh=0, signeddist=True
        )
        ms.set_current_mesh(1)
        # Extract signed distance field
        d = ms.current_mesh().vertex_scalar_array()
        points = ms.current_mesh().vertex_matrix().T
        # Keep only points which lie outside soma
        keep = d > 0

        # Update points
        for i, flag in enumerate(keep):
            if ~flag:
                keep[i] = ~_in_aabb(soma_aabb, points[:, i])
        points = points[:, keep]

        # Merge meshes
        if includemesh:
            p, _, _ = soma.output()
            points = [points, p]
            points = np.concatenate(points, axis=1)
        ms.clear()

        # Create new mesh.
        m = mlab.Mesh(
            vertex_matrix=points.T,
        )
        ms = mlab.MeshSet()
        ms.add_mesh(m)

        # Remove any duplicates
        ms.meshing_remove_duplicate_vertices()
        return ms

    @staticmethod
    def _parent_child_intersect(seg, p, c, remove_close_points=False) -> None:
        """Remove collision points in the parent and child nodes.

        Args:
            seg (list): list of segments.
            p (int): parent index in `seg`.
            c (int): child index in `seg`.
            remove_close_points (bool, optional): If this is set to True,
            remove all the points that are nearer than the specified threshold.
            Defaults to False.
        """

        # update parent
        [_, p_on, p_outer, p_out_near] = seg[c].intersect(seg[p])
        seg[p].update(np.logical_or(p_on, p_outer))

        # update child
        [_, _, c_outer, c_out_near] = seg[p].intersect(seg[c])
        seg[c].update(c_outer)

        if remove_close_points:
            # get minimum radius
            r_mins = []
            for i in [p, c]:
                if hasattr(seg[i], "r_min"):
                    r_mins.append(seg[i].r_min)
                else:
                    r_mins.append(seg[i].r)
            r_min = min(r_mins)

            # get points and normals
            p_points, p_normals, _ = seg[p].output(p_out_near)
            c_points, c_normals, _ = seg[c].output(c_out_near)

            # compute distance between two point clouds
            p_points = p_points.T.reshape((-1, 1, 3))
            c_points = c_points.T.reshape((1, -1, 3))
            dist = np.linalg.norm(p_points - c_points, axis=2)

            # compute angle between normals
            angle = p_normals.T @ c_normals

            # remove close points
            mask_far = (dist >= 0.1 * r_min) | (angle >= 0)
            mask_far = mask_far & (dist >= 0.02 * r_min)
            if not mask_far.all():
                p_mask = np.all(mask_far, axis=1)
                c_mask = np.all(mask_far, axis=0)

                # remove parent's points
                p_keep = dcp(seg[p].keep)
                p_keep[p_keep & p_out_near] = p_mask
                seg[p].update(p_keep)

                # remove child's points
                c_keep = dcp(seg[c].keep)
                c_keep[c_keep & c_out_near] = c_mask
                seg[c].update(c_keep)

        return None

    @staticmethod
    def aabb(seg):
        """Get the aabb collision index pairs."""

        # get all indices
        indices = [(i, j) for i in range(len(seg) - 1) for j in range(i + 1, len(seg))]

        # get axis-aligned bounding box
        aabbs = [iseg.aabb for iseg in seg]
        aabb_pairs = [(aabbs[i], aabbs[j]) for i, j in indices]

        # detect aabb collision
        with Pool() as p:
            flags = p.map(_aabb_collision, aabb_pairs)
        collision_index_pairs = []

        # assemble the collision index pairs
        for ind, flag in enumerate(flags):
            if flag:
                collision_index_pairs.append(indices[ind])

        return collision_index_pairs


def get_bbox_diag(p):
    """Returns diagonal of a bounding box for point cloud p
    Args:
        p: (N,3) array of floats
    Returns:
        diag: (float)
    """
    min_x = min(p[:, 0])
    min_y = min(p[:, 1])
    min_z = min(p[:, 2])
    max_x = max(p[:, 0])
    max_y = max(p[:, 1])
    max_z = max(p[:, 2])
    diag = np.sqrt((max_x - min_x) ** 2 + (max_y - min_y) ** 2 + (max_z - min_z) ** 2)
    if diag == 0:
        raise ValueError("Only one point in point cloud")
    return diag


def extract_swc(file):
    """Extracts the position data, radius data, connectivity data and the type data from a swc file
    Args:
        file: (string) swc file to be read.
    Returns:
        position_data: (N,3) array of floats of 3d postitions of nodes.
        radius_data: (N,) array of positive floats of cross-sectional radii of nodes.
        conn_data: (N,2) array of intergers of child parent pairs of nodes.
        type_data: (N,) array of intergers of the type of each node.
        preamble: string array of initial lines from swc file.

    """

    position_data = []
    radius_data = []
    conn_data = []
    type_data = []
    preamble = []

    # parse swc file
    with open(file, "r") as f:
        first_node = True
        found_scale = False
        reset_radii = []
        for iline in f:
            line = iline.strip().lower().split()

            # get the scale
            if "scale" in line:
                if line[0] == "#":
                    scale = np.array(line[2:5], dtype=float)
                else:
                    scale = np.array(line[1:4], dtype=float)
                found_scale = True
            # read nodes
            elif len(line) == 7 and line[0].isnumeric():
                # check the parent compartment of the first node
                if not (found_scale):
                    scale = np.array([1, 1, 1])
                    found_scale = True

                if first_node and int(line[6]) != -1:
                    raise ValueError("Parent of the first node must be -1.")
                else:
                    first_node = False

                # extract info
                id = int(line[0]) - 1
                node_type = int(line[1])
                position = scale * np.array(line[2:5], dtype=float)
                radius = float(line[5])
                parent_id = int(line[6]) - 1

                # check parameters
                if parent_id < 0:
                    parent_id = -1

                if parent_id == -1 and node_type != 1:
                    node_type = -1
                    msg = "Soma absent. Convert the first point to synthetic soma."
                    warnings.warn(msg, RuntimeWarning, stacklevel=2)

                if id < 0:
                    msg = f"Node id {line[0]}: negative compartment ID."
                    raise ValueError(msg)

                if radius < 1e-4:
                    msg = f"Node id {line[0]}: radius to small, reset the scale of swc file. Setting to parent radius"
                    warnings.warn(msg, Warning)
                    reset_radii.append(id)
                elif radius < 0:
                    msg = f"Node id {line[0]}: negative radius."
                    radius = -radius
                    warnings.warn(msg, Warning)
                # if radius < 0.1:
                #     radius = 0.1

                if node_type < -1 or node_type > 7:
                    msg = " ".join((f"Node id {line[0]}:", "unknown compartment type."))
                    warnings.warn(msg, Warning)

                # record info
                position_data.append(position)
                type_data.append(node_type)
                radius_data.append(radius)
                conn_data.append(np.array([id, parent_id]))
            else:
                preamble.append(iline)

    for id in reset_radii:
        if conn_data[id][1] != -1:
            radius_data[id] = radius_data[conn_data[id][1]]
        else:
            msg = f"File is corrupt at node {id+1}"
            raise ValueError(msg)

    position_data = np.array(position_data)
    type_data = np.array(type_data)
    radius_data = np.array(radius_data)
    conn_data = np.array(conn_data)
    return position_data, radius_data, conn_data, type_data, preamble


def add_node_between_parent(
    i, num_points, position_data, radius_data, conn_data, type_data
):
    """Adds linearly interpolated node between a node i and it's parent
    Args:
        i: (int) node to be merged with parent.
        num_points: (int) number of nodes to be inserted.
        position_data: (N,3) array of floats of 3d postitions of nodes.
        radius_data: (N,) array of positive floats of cross-sectional radii of nodes.
        conn_data: (N,2) array of intergers of child parent pairs of nodes.
        type_data: (N,) array of intergers of the type of each node.

    Returns:
        new_position_data: (N+num_points,3) array of floats of 3d postitions of nodes.
        new_radius_data: (N+num_points,) array of positive floats of cross-sectional radii of nodes.
        new_conn_data: (N+num_points,2) array of intergers of child parent pairs of nodes.
        new_type_data: (N+num_points,) array of intergers of the type of each node.

    """
    N = len(position_data) + num_points
    parent_id = conn_data[i][1]
    p = position_data[i]
    q = position_data[parent_id]
    r = radius_data[i]
    R = radius_data[parent_id]
    new_position_data = np.zeros((N, 3))
    new_radius_data = np.zeros(N)
    new_type_data = np.zeros(N)
    new_conn_data = np.zeros((N, 2))

    new_position_data[0:i] = position_data[0:i]
    new_radius_data[0:i] = radius_data[0:i]
    new_type_data[0:i] = type_data[0:i]
    new_conn_data[0 : (i + 1)] = conn_data[0 : (i + 1)]

    for j in range(0, num_points):
        l = (j + 1) / (num_points + 1)
        new_position_data[(j + i)] = (1 - l) * q + l * p
        new_radius_data[j + i] = R ** ((1 - l)) * r**l
        new_conn_data[j + 1 + i] = np.array([j + 1 + i, i + j])
    new_type_data[i : (i + num_points)] += type_data[i]
    new_position_data[i + num_points :] = position_data[i:]
    new_radius_data[i + num_points :] = radius_data[i:]
    new_type_data[i + num_points :] = type_data[i:]

    new_conn_data[(1 + i + num_points) :, 1] = conn_data[1 + i :, 1]
    new_conn_data[(1 + i + num_points) :, 0] = conn_data[1 + i :, 0] + num_points

    for j in range(i + num_points + 1, N):
        if new_conn_data[j, 1] >= i:
            new_conn_data[j, 1] = new_conn_data[j, 1] + num_points

    return (
        new_position_data,
        new_radius_data,
        np.array(new_conn_data, dtype=int),
        np.array(new_type_data, dtype=int),
    )


def node_merge_with_parent(i, position_data, radius_data, conn_data, type_data):
    """Merges a node i with it's parent
    Args:
        i: (int) node to be merged with parent.
        position_data: (N,3) array of floats of 3d postitions of nodes.
        radius_data: (N,) array of positive floats of cross-sectional radii of nodes.
        conn_data: (N,2) array of intergers of child parent pairs of nodes.
        type_data: (N,) array of intergers of the type of each node.

    Returns:
        new_position_data: (N-1,3) array of floats of 3d postitions of nodes.
        new_radius_data: (N-1,) array of positive floats of cross-sectional radii of nodes.
        new_conn_data: (N-1,2) array of intergers of child parent pairs of nodes.
        new_type_data: (N-1,) array of intergers of the type of each node.

    """
    N = len(position_data) - 1
    parent_id = conn_data[i][1]
    p = position_data[i]
    q = position_data[parent_id]
    r = radius_data[i]
    R = radius_data[parent_id]

    mean_position = (p + q) / 2
    mean_radius = np.sqrt(r * R)

    new_position_data = np.zeros((N, 3))
    new_radius_data = np.zeros(N)
    new_type_data = np.zeros(N)
    new_conn_data = np.zeros((N, 2))

    new_position_data[0:i] = position_data[0:i]
    new_radius_data[0:i] = radius_data[0:i]
    new_type_data[0:i] = type_data[0:i]
    new_conn_data[0:i] = conn_data[0:i]

    new_position_data[parent_id] = mean_position
    new_radius_data[parent_id] = mean_radius

    new_position_data[i:] = position_data[(1 + i) :]
    new_radius_data[i:] = radius_data[(1 + i) :]
    new_type_data[i:] = type_data[(1 + i) :]
    new_conn_data[i:] = conn_data[(1 + i) :]

    new_conn_data[i:, 0] = new_conn_data[i:, 0] - 1

    for j in range(i, N):
        if new_conn_data[j, 1] > i:
            new_conn_data[j, 1] = new_conn_data[j, 1] - 1
        elif new_conn_data[j, 1] == i:
            new_conn_data[j, 1] = parent_id
    return (
        new_position_data,
        new_radius_data,
        np.array(new_conn_data, dtype=int),
        np.array(new_type_data, dtype=int),
    )


def smooth_swc(position_data, radius_data, conn_data, type_data, Delta):
    """Smooths the swc file, by iterating through it and merging and inserting nodes
    Args:
        position_data: (N,3) array of floats of 3d postitions of nodes.
        radius_data: (N,) array of positive floats of cross-sectional radii of nodes.
        conn_data: (N,2) array of intergers of child parent pairs of nodes.
        type_data: (N,) array of intergers of the type of each node.
        Delta: (float) postive smoothing distance.

    Returns:
        position_data: (N,3) array of floats of 3d postitions of nodes.
        radius_data: (N,) array of positive floats of cross-sectional radii of nodes.
        conn_data: (N,2) array of intergers of child parent pairs of nodes.
        type_data: (N,) array of intergers of the type of each node.

    """
    N = len(position_data)
    # For efficiency, number of children are calculated once, and then updated as nodes are inserted/added.
    num_children = [int(sum(conn_data[:, 1] == i)) for i in range(0, N)]
    i = 0
    while i < N:
        p = position_data[i]
        # Check node is not a soma node or direct child of soma node.
        if (
            conn_data[i][1] >= 0
            and type_data[i] != 1
            and type_data[conn_data[i][1]] != 1
        ):
            parent_id = conn_data[i][1]
            q = position_data[parent_id]
            r = radius_data[i]
            R = radius_data[parent_id]
            radius_ratio_flag = r / R > 2 or R / r > 2
            num_siblings = num_children[parent_id] - 1
            if (
                norm(p - q) < Delta
                and num_children[i] == 1
                and num_siblings == 0
                and not (radius_ratio_flag)
            ):
                # Merge nodes
                position_data, radius_data, conn_data, type_data = (
                    node_merge_with_parent(
                        i, position_data, radius_data, conn_data, type_data
                    )
                )
                N = N - 1
                num_children.pop(i)
            elif radius_ratio_flag:
                # Add interpolated nodes as radii change drastically
                num_points = int(np.min([3, np.floor(np.max([r / R, R / r]))]))
                position_data, radius_data, conn_data, type_data = (
                    add_node_between_parent(
                        i, num_points, position_data, radius_data, conn_data, type_data
                    )
                )
                i = i + num_points + 1
                N = N + num_points
                for j in range(0, num_points):
                    num_children.insert(i + j, 1)

            elif norm(p - q) > 2 * Delta:
                # Add interpolated nodes as nodes too far apart
                num_points = int(np.min([3, np.floor(norm(p - q) / Delta - 1)]))
                position_data, radius_data, conn_data, type_data = (
                    add_node_between_parent(
                        i, num_points, position_data, radius_data, conn_data, type_data
                    )
                )
                i = i + num_points + 1
                N = N + num_points
                for j in range(0, num_points):
                    num_children.insert(i + j, 1)

            elif norm(p - q) < 1e-5:
                # Nodes are too close, must merge nodes.
                position_data, radius_data, conn_data, type_data = (
                    node_merge_with_parent(
                        i, position_data, radius_data, conn_data, type_data
                    )
                )
                N = N - 1
                num_children.pop(i)

            else:
                i += 1
        else:
            i += 1
    return position_data, radius_data, conn_data, type_data


def interpolate_swc(position_data, radius_data, conn_data, type_data, delta):
    """Pass through swc nodes, inserting nodes where they are required.
    Insertions are required when:
     - adjacent nodes are more than delta apart
     - two nodes each with multiple children would not intersect each other when represented as spheres.

    Args:
        position_data: (N,3) array of floats of 3d postitions of nodes.
        radius_data: (N,) array of positive floats of cross-sectional radii of nodes.
        conn_data: (N,2) array of intergers of child parent pairs of nodes.
        type_data: (N,) array of intergers of the type of each node.
        delta: (float) postive interpolation distance.

    Returns:
        position_data: (N,3) array of floats of 3d postitions of nodes.
        radius_data: (N,) array of positive floats of cross-sectional radii of nodes.
        conn_data: (N,2) array of intergers of child parent pairs of nodes.
        type_data: (N,) array of intergers of the type of each node.

    """

    i = -1
    N = len(position_data)
    num_children = [int(sum(conn_data[:, 1] == i)) for i in range(0, N)]
    while i < N - 1:
        i = i + 1
        if conn_data[i][1] != -1 and type_data[i] != 1:
            p = position_data[i]
            parent_id = conn_data[i][1]
            q = position_data[parent_id]
            r_min = min([radius_data[i], radius_data[parent_id]])
            if norm(p - q) >= delta or (
                norm(p - q) >= r_min
                and num_children[i] > 1
                and num_children[parent_id] > 1
            ):
                "Add interpolated nodes"
                num_points = max([int(np.floor(norm(p - q) / delta - 1)), 1])
                position_data, radius_data, conn_data, type_data = (
                    add_node_between_parent(
                        i, num_points, position_data, radius_data, conn_data, type_data
                    )
                )
                for j in range(0, num_points):
                    num_children.insert(i + j, 1)
                i = i + num_points
                N = N + num_points

    return position_data, radius_data, conn_data, type_data


def create_branches(conn_data, type_data):
    """Passes through the swc file and returns a classification of all nodes into branches or junctions.
    A junction node i will have branches[i] = -1. A node i in branche j will have branches[i] = j.
    Args:
        conn_data: (N,2) array of intergers of child parent pairs of nodes.
        type_data: (N,) array of intergers of the type of each node.
    Returns:
        branches: (N,) array of intergers representing the segment to which each node belongs.
    """

    N = len(conn_data)
    branches = np.zeros(N, dtype=int)
    id = 1
    children = [np.where(conn_data[:, 1] == i)[0] for i in range(0, N)]
    num_children = [len(c) for c in children]
    junction_ind = [
        i
        for (i, n) in enumerate(num_children)
        if n > 1 or type_data[i] == 1 or type_data[i] == -1
    ]
    i = 0
    while i < N:
        if i in junction_ind:
            branches[i] = -1
        elif branches[i] == 0:
            j = i
            while branches[j] == 0 and num_children[j] <= 1:
                branches[j] = id
                if num_children[j] == 1:
                    j = children[j][0]
                else:
                    break
            id += 1
        i += 1

    return branches


def reorder_swc(position_data, radius_data, conn_data, type_data):
    """Reorders nodes to ensure parents always come before children.

    Args:
        position_data: (N,3) array of floats of 3d postitions of nodes.
        radius_data: (N,) array of positive floats of cross-sectional radii of nodes.
        conn_data: (N,2) array of intergers of child parent pairs of nodes.
        type_data: (N,) array of intergers of the type of each node.

    Returns:
        position_data: (N,3) array of floats of 3d postitions of nodes.
        radius_data: (N,) array of positive floats of cross-sectional radii of nodes.
        conn_data: (N,2) array of intergers of child parent pairs of nodes.
        type_data: (N,) array of intergers of the type of each node.

    """
    print("Reordering swc")
    # Identify source node
    N = len(conn_data)
    nodes = conn_data[:, 0]
    parents = conn_data[:, 1]
    source = nodes[parents == -1]
    # if len(source) > 1:
    #     msg = f'swc file has {len(source)} source nodes.'
    #     raise ValueError(msg)

    # Initialise a permutation which will send the source node to the first position.
    # New data will be given by new_data = original_data[permutation]
    # permutation = np.zeros(N)
    # permutation[source] = 0
    # permutation[0] = source
    # set= 0
    # start_node = 0

    # # Create permutation
    # permutation,_ = reorder(start_node,set,nodes,parents,permutation)

    permutation = np.zeros(N)
    # permutation[source[0]] = 0
    permutation[0] = source[0]
    set = -1

    recursion_limit = sys.getrecursionlimit()
    if N > recursion_limit:
        warnings.warn(
            f"Temporarily Increasing python recusion limit from {recursion_limit} to {N}"
        )
        sys.setrecursionlimit(N)
    # Create permutation
    for i in source:
        set = set + 1
        permutation[set] = i
        permutation, set = reorder(i, set, nodes, parents, permutation)
    sys.setrecursionlimit(recursion_limit)
    permutation = np.array(permutation).astype(int)
    # Reorder data based on this permutation
    conn_data = conn_data[permutation]
    for i in range(0, N):
        mask = conn_data == conn_data[i, 0]
        mask2 = conn_data == i
        conn_data[mask2] = conn_data[i, 0]
        conn_data[mask] = i

    position_data = position_data[permutation]
    type_data = type_data[permutation]
    radius_data = radius_data[permutation]

    return position_data, radius_data, conn_data, type_data


def reorder(start_node, set, nodes, parents, permutation):
    """A recursive function to build the permutation to reorder the swc file.
    Args:
        start_node: (int) node under consideration. It has already been correctly ordered.
        set: (int) the number of nodes already considered. This is also the value, permutation[set] = start_node.
        nodes: (N,) array of intergers of the node indices.
        parents: (N,) array of intergers of the parent node indices.
        permutation: (N,) array of intergers representing a permutation in S_n.
    Returns:
        permutation: Updated (N,) array of intergers representing a permutation in S_n.
        set: (int) Updated number of nodes already considered.
    """
    # Find children
    children = np.where(parents == start_node)[0]
    for i in range(0, len(children)):
        set = set + 1
        permutation[set] = children[i]
        permutation, set = reorder(children[i], set, nodes, parents, permutation)
    return permutation, set


def _in_aabb(aabb, p):
    """Detect if point p is in Axis-aligne Bouding Box aabb"""
    xa, ya, za = aabb
    x = p[0]
    y = p[1]
    z = p[2]

    return (
        xa["min"] <= x
        and x <= xa["max"]
        and ya["min"] <= y
        and y <= ya["max"]
        and za["min"] <= z
        and z <= za["max"]
    )


def _aabb_collision(aabb_pair):
    """Detect "Axis-Aligned Bounding Box" collision."""

    xa, ya, za = aabb_pair[0]
    xb, yb, zb = aabb_pair[1]

    # no collision
    if (
        xa["max"] <= xb["min"]
        or xa["min"] >= xb["max"]
        or ya["max"] <= yb["min"]
        or ya["min"] >= yb["max"]
        or za["max"] <= zb["min"]
        or za["min"] >= zb["max"]
    ):
        return False

    # found collision
    else:
        return True
