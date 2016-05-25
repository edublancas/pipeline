import hashlib
import re


def class_name(obj):
    class_name = str(type(obj))
    class_name = re.search(".*'(.+?)'.*", class_name).group(1)
    return class_name


def _can_iterate(obj):
    import types
    import collections

    is_string = isinstance(obj, types.StringTypes)
    is_iterable = isinstance(obj, collections.Iterable)

    return is_iterable and not is_string


# based on:
#   http://stackoverflow.com/questions/5386694/fast-way-to-hash-numpy-objects-for-caching
#   http://stackoverflow.com/questions/806151/how-to-hash-a-large-object-dataset-in-python
def hash_sha1_numpy_array(a):
    '''
        Hash a numpy array using sha1.
    '''
    import numpy as np
    # conver to contigous in case the array has a different
    # representation
    a = np.ascontiguousarray(a)
    # get a view from the array, this will help produce different hashes
    # for arrays with same data but different shapes
    a = a.view(np.uint8)
    return hashlib.sha1(a).hexdigest()
