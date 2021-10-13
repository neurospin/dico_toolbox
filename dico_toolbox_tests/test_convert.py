from soma import aims
import dico_toolbox as dtb

def test_volume_to_mesh():
    bck_path = "test_data/bucket.bck"
    bck = aims.read(bck_path)[0]
    vol = dtb.convert.bucket_aims_to_volume_numpy(bck)

    mesh = dtb.convert.volume_to_mesh(vol)