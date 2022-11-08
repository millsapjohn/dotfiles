set SAGA=C:/PROGRA~1/QGIS32~2.3/apps\saga
set SAGA_MLB=C:/PROGRA~1/QGIS32~2.3/apps\saga\modules
PATH=%PATH%;%SAGA%;%SAGA_MLB%
call saga_cmd shapes_lines "Convert Points to Line(s)"  -POINTS "C:/Users/JohnMillsap/AppData/Local/Temp/processing_RFhlIO/3ac69dbb64f74296ac2472928b74b326/POINTS.shp" -ORDER "field_1" -SEPARATE "field_1" -ELEVATION "field_1" -LINES "C:/Users/JohnMillsap/AppData/Local/Temp/processing_RFhlIO/cc312514f8424368a270d7e5108de0f5/LINES.shp"
exit