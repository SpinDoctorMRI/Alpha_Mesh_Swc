#!/usr/bin/env python
import numpy as np
import trimesh as tm
from trimesh import viewer,Trimesh
import argparse
import pymeshlab as mlab

def apply_transform(affine, points):
    return np.dot(points, affine[:3, :3].T) + affine[np.newaxis, 3, :3]


def rotation_x(angle):
    return np.array([[1.0,            0.0,           0.0],
                     [0.0, np.cos(angle), -np.sin(angle)],
                     [0.0, np.sin(angle),  np.cos(angle)]])


def rotation_y(angle):
    return np.array([[ np.cos(angle), 0.0, np.sin(angle)],
                     [           0.0, 1.0,           0.0],
                     [-np.sin(angle), 0.0, np.cos(angle)]])


def rotation_z(angle):
    return np.array([[np.cos(angle), -np.sin(angle), 0.0],
                     [np.sin(angle),  np.cos(angle), 0.0],
                     [          0.0,            0.0, 1.0]])


def draw_swc(filename):
    """This function parses a SWC file and creates trimesh primitives."""
    data = np.loadtxt(filename)
    primitives = []
    nb_nodes = data.shape[0]
    for i in range(nb_nodes):
        index, swc_type, x, y, z, radius, predecessor = data[i]
        sphere = create_sphere(radius, np.array([x, y, z]), subdivisions=2)
        primitives.append(sphere)
        if predecessor != -1:
            predecessor = int(predecessor) - 1
            radius1 = radius
            radius2 = data[predecessor, 5]
            segment = data[[i, predecessor], 2:5]
            cone = create_truncated_cone(segment, radius1, radius2)
            primitives.append(cone)
    return primitives


def normalize_cylinder(segment):
    """
    Returns
    -------
    transform : array-like, shape (4, 4)
        Affine transform from the normalized cylinder to the original.
    """
    axis = segment[1] - segment[0]
    axis /= np.linalg.norm(axis)
    center = np.mean(segment, axis=0)
    theta = np.arccos(axis[2])
    phi = np.arctan2(axis[1], axis[0])
    transform = np.eye(4)
    transform[:3, :3] = np.dot(rotation_z(phi), rotation_y(theta))
    transform[3, :3] = center
    return transform


def normalized_cylinder_random(nb_particles, height, radius):
    z = np.random.uniform(low=-height / 2, high=height / 2, 
                          size=(nb_particles,))
    phis = np.random.uniform(low=0, high=2 * np.pi, size=(nb_particles,))
    r = np.sqrt(np.random.uniform(0, 1, size=nb_particles)) * radius
    return np.array([r * np.cos(phis), r * np.sin(phis), z]).T


def create_truncated_cone(segment, radius1, radius2, sections=10):
    """Computes a triangular mesh of a cylinder.
    """
    # First compute the (approximate) triangle edge length
    radius = min(radius1, radius2)
    a = 2 * radius * np.pi / sections
    height = np.linalg.norm(segment[1] - segment[0])
    nb_floors = max(int(height / a), 1)
    angles = np.linspace(0, 2 * np.pi, sections + 1)[:sections]
    z = np.linspace(-height / 2, height / 2, nb_floors + 1)
    vertices = np.zeros((nb_floors + 1, sections, 3))
    radii = np.linspace(radius1, radius2, nb_floors + 1)
    vertices[:, :, 0] = radii[:, np.newaxis] * np.cos(angles[np.newaxis, :])
    vertices[:, :, 1] = radii[:, np.newaxis] * np.sin(angles[np.newaxis, :])
    vertices[:, :, 2] = z[:, np.newaxis]
    vertices = vertices.reshape(((nb_floors + 1) * sections, 3))
    vertices = np.append(vertices, [[0, 0, -height / 2], [0, 0, height / 2]],
                         axis=0)
    triangles = []
    for floor in range(nb_floors):
        for section in range(sections):
            next_section = (section + 1) % sections
            a = np.ravel_multi_index([floor, section], 
                                 (nb_floors + 1, sections))
            b = np.ravel_multi_index([floor, next_section], 
                                 (nb_floors + 1, sections))
            c = np.ravel_multi_index([floor + 1, next_section], 
                                 (nb_floors + 1, sections))
            d = np.ravel_multi_index([floor + 1, section], 
                                 (nb_floors + 1, sections))
            triangles.append([a, b, c])
            triangles.append([d, a, c])
    for section in range(sections):
        next_section = (section + 1) % sections
        c = vertices.shape[0] - 2
        a = np.ravel_multi_index([0, section], (nb_floors + 1, sections))
        b = np.ravel_multi_index([0, next_section], (nb_floors + 1, sections))
        triangles.append([c, b, a])
    for section in range(sections):
        next_section = (section + 1) % sections
        c = vertices.shape[0] - 1
        a = np.ravel_multi_index([nb_floors, section], (nb_floors + 1, sections))
        b = np.ravel_multi_index([nb_floors, next_section], (nb_floors + 1, sections))
        triangles.append([a, b, c])
    transform = normalize_cylinder(segment)
    vertices = apply_transform(transform, vertices)
    kwargs = dict()
    kwargs['metadata'] = dict()
    kwargs['metadata'].update(
        {'shape': 'cylinder',
         'height': height,
         'radius': radius,
         'segment': segment})
 
    mesh = tm.Trimesh(vertices=vertices, faces=triangles, **kwargs)
    points = tm.points.PointCloud(vertices)
    return mesh
    

def create_sphere(radius, center, subdivisions=1):
    mesh = tm.creation.icosphere(radius=radius, subdivisions=subdivisions)
    transform = np.eye(4)
    transform[:3, 3] = center
    mesh.apply_transform(transform)
    mesh.metadata.update({"shape": "sphere", 
                          "radius": radius, "center": center})
    return mesh


def _in_cylinder(radius, segment, points):
    a, b = segment
    height = np.linalg.norm(b - a)
    axis = (b - a) / height
    dotprods = np.dot(points - a[np.newaxis, :], axis)
    projections = a + dotprods[:, np.newaxis] * axis[np.newaxis, :]
    distances = np.linalg.norm(points - projections, axis=1)
    return (dotprods > 0) & (dotprods < height) & (distances < radius)

def _in_sphere(radius, center, points):
    distances = np.linalg.norm(points - center[np.newaxis, :], axis=1)
    return distances < radius


def in_primitive(primitive, points):
    if primitive.metadata["shape"] == "sphere":
        return _in_sphere(primitive.metadata["radius"],
                          primitive.metadata["center"],
                          points)
    if primitive.metadata["shape"] == "cylinder":
        return _in_cylinder(primitive.metadata["radius"],
                            primitive.metadata["segment"],
                            points)
    raise ValueError("Unsupported primitive type.")

def mlab2tmesh(ms):
    """Convert Meshlab mesh to Trimesh object.

    Args:
        ms (mlab.MeshSet, mlab.Mesh): Meshlab mesh.

    Raises:
        TypeError: wrong mesh type.

    Returns:
        Trimesh: Trimesh object.
    """

    # check mesh type
    if isinstance(ms, mlab.MeshSet):
        m = ms.current_mesh()
    elif isinstance(ms, mlab.Mesh):
        m = ms
    else:
        raise TypeError("Unknown mesh type.")

    # convert mlab.Mesh to Trimesh
    tmesh = Trimesh(
        process=False,
        use_embree=False,
        vertices=m.vertex_matrix(),
        faces=m.face_matrix(),
        face_normals=m.face_normal_matrix(),
        vertex_normals=m.vertex_normal_matrix(),
        vertex_colors=m.vertex_color_matrix()
    )

    return tmesh



if __name__ == "__main__":

    description = """Reads a SWC file and visualize using trimesh."""

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("input", help="Input SWC file.")
    parser.add_argument("--soma", help ="Optionally input separate soma file",default=None)
    args = parser.parse_args()
    

    primitives = draw_swc(args.input)

    if args.soma is not None:
        ms = mlab.MeshSet()
        ms.load_new_mesh(args.soma)
        soma = mlab2tmesh(ms)
        primitives.append(soma)

    scene = tm.scene.Scene(primitives)
    viewer = tm.viewer.windowed.SceneViewer(scene, flags={"wireframe": False})
