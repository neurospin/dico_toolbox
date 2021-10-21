import dico_toolbox as dtb

def test_list_buckets():
    graph_path = "test_data/graph.bck"
    buckets = dtb.graph.list_buckets(graph_path, transform="Talairach")
