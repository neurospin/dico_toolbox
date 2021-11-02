import dico_toolbox as dtb


def test_list_buckets():
    graph_path = dtb.test_data.bv_database().get(type="graph")[0]
    buckets = dtb.graph.list_buckets(graph_path, transform="Talairach")
