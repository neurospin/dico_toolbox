import dico_toolbox as dtb


def test_list_buckets():
    graph_path = dtb.database.create_test_database().get(type="graph")[0]
    buckets = dtb.graph.list_buckets(graph_path, transform="Talairach")
