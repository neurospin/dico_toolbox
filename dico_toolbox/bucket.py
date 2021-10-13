import numpy as _np
from soma import aims as _aims

def flip_bucket(bucket, axis=0):
    """flip a bucket and return a new flipped instance."""
    if isinstance(bucket, _aims.BucketMap_VOID.Bucket):
        raise ValueError("not yet implemented for aims buckets, use numpy buckets")
        # out = _aims.BucketMap()
        # for point in bucket.keys():
        #     print("point", point.arraydata())
        #     v = point.arraydata()
        #     v[axis]*=-1
        #     out[v] = 1
    elif isinstance(bucket, _np.ndarray) and bucket.shape[1] == 3:
        out = bucket.copy()
        out[:,axis] *= -1
    else:
        raise ValueError("Unknown bucket type")
    
    return out