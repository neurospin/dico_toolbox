# [treesource] topological values of Aims skeletons

# cfr. : [brainvisa]/src/morphologist/morphologist-private/bug_fix/vip/src/libvip/topology.h
# reference : 1995 - JF Mangin et Al. From 3D magneti resonance images to structural ... Figure.12
topological_values = {
    'interior': 0,                 # [?] below gray matter
    'volume': 10,                  # [A] volume point
    'isolated': 20,                # [B] isolated point
    'exterior': 11,                # [?] above gray matter
    'border': 30,                  # [C] boder of a sulcus-element surface
    'curve': 40,                   # [D] 1D curve
    'curve_curve-junction': 50,    # [E] intersection of two curves
    'surface': 60,                 # [F] surface of a sulcus-element
    # [G] intersection of a curve and a surface
    'curve_surface-junction': 70,
    'surfaces-junction': 80,       # [H] intersection of several surfaces
    # [I] intersection of several surfaces and a curve
    'surfaces_curve-junction': 90
}


class topovalues:
    bottom = topological_values['border']
    surface = topological_values['surface']
    interior = topological_values['interior']
    exterior = topological_values['exterior']


topological_values_by_value = dict((v, k)
                                   for k, v in topological_values.items())
