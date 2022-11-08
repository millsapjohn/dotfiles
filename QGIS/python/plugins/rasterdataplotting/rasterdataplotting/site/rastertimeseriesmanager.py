try:
    from rastertimeseriesmanager.rastertimeseriesmanager.gui.rtmrastertimeseriesbandcombobox import RtmRasterTimeseriesBandComboBox
    from rastertimeseriesmanager.rastertimeseriesmanager.gui.rtmrastertimeseriesdatecombobox import RtmRasterTimeseriesDateComboBox
    from rastertimeseriesmanager.rastertimeseriesmanager.core.rtmrastertimeseries import RtmRasterTimeseries
    from rastertimeseriesmanager import rtmInterface
    rtmInstalled = True
except:
    from qgis.PyQt.QtWidgets import QComboBox
    RtmRasterTimeseriesBandComboBox = QComboBox
    RtmRasterTimeseriesDateComboBox = QComboBox
    RtmRasterTimeseries = type(None)
    rtmInterface = lambda raiseError=True: None
    rtmInstalled = False
