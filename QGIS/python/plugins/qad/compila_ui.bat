set OSGEO4W_ROOT=C:\Program Files\QGIS 3.10

call "%OSGEO4W_ROOT%\bin\o4w_env.bat"
call "%OSGEO4W_ROOT%\bin\qt5_env.bat"
call "%OSGEO4W_ROOT%\bin\py3_env.bat"

path %OSGEO4W_ROOT%\apps\bin;%OSGEO4W_ROOT%\apps\grass\grass76\lib;%OSGEO4W_ROOT%\apps\grass\grass76\bin;%PATH%

cd /d %~dp0

@ECHO ON
call pyuic5 --from-imports -o qad_ui.py qad.ui
call pyuic5 --from-imports -o .\qad_dsettings_ui.py .\qad_dsettings.ui
call pyuic5 --from-imports -o .\qad_pointerinput_settings_ui.py .\qad_pointerinput_settings.ui
call pyuic5 --from-imports -o .\qad_dimensioninput_settings_ui.py .\qad_dimensioninput_settings.ui
call pyuic5 --from-imports -o .\qad_dimstyle_ui.py .\qad_dimstyle.ui
call pyuic5 --from-imports -o .\qad_dimstyle_details_ui.py .\qad_dimstyle_details.ui
call pyuic5 --from-imports -o .\qad_dimstyle_new_ui.py .\qad_dimstyle_new.ui
call pyuic5 --from-imports -o .\qad_dimstyle_diff_ui.py .\qad_dimstyle_diff.ui
call pyuic5 --from-imports -o .\qad_options_ui.py .\qad_options.ui
call pyuic5 --from-imports -o .\qad_gripcolor_ui.py .\qad_gripcolor.ui
call pyuic5 --from-imports -o .\qad_windowcolor_ui.py .\qad_windowcolor.ui
call pyuic5 --from-imports -o .\qad_tooltip_appearance_ui.py .\qad_tooltip_appearance.ui
call pyuic5 --from-imports -o .\qad_rightclick_ui.py .\qad_rightclick.ui
