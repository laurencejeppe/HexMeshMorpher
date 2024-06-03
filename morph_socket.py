
import morph_liner as ml

ml.FOLDER = 'Socket_Designs'

socket = ml.STLMesh('Rectified Socket', 'Rectified_realigned', load=True)

print(socket.f_path)

liner_surface = ml.load_liner_surface(from_inp=True)

boundary_nodes = liner_surface.get_boundary_nodes(check_plot=False)

num_rim_nodes = len(boundary_nodes['indices'])

polygon = ml.PolygonResample(socket, num_rim_nodes, False)

landmarks = [[node_num, polygon.interp_array[i]] \
             for i, node_num in enumerate(boundary_nodes['indices'])]

socket_surface_mapped = 