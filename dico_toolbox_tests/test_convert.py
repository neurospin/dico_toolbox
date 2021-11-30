from soma import aims
import dico_toolbox as dtb
import resources


def test_volume_to_mesh():
    bckMap = resources.data.bucket_example
    bck = bckMap[0]
    vol, _ = dtb.convert.bucket_aims_to_volume_numpy(bck)

    try:
        _ = dtb.convert.volume_to_mesh(vol)

    except Exception as e:
        raise Exception(f"Error generating mesh: {str(e)}")
