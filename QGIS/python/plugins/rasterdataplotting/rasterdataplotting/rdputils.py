import os
import numpy as np
from qgis.core import Qgis


def version():
    metadata = os.path.abspath(os.path.join(__file__, '..', '..', 'metadata.txt'))
    with open(metadata) as f:
        for line in f.readlines():
            if line.startswith('version='):
                return line.split('=')[1].strip()

def qgisDataTypeToNumpyDataType(dataType):

    if dataType == Qgis.Byte:
        return np.uint8
    elif dataType == Qgis.Float32:
        return np.float32
    elif dataType == Qgis.Float64:
        return np.float64
    elif dataType == Qgis.Int16:
        return np.int16
    elif dataType == Qgis.Int32:
        return np.int32
    elif dataType == Qgis.UInt16:
        return np.uint16
    elif dataType == Qgis.UInt32:
        return np.uint32
    elif dataType == Qgis.UnknownDataType:
        return None
    else:
        raise Exception('unsupported data type: {}'.format(dataType))

def toFloat(s, default=0):
    try:
        return float(s)
    except:
        return default
