@echo off

pdoc3 -c show_source_code=False -c show_inherited_members=True -c show_type_annotations=True --html  --force --output-dir ./docs/code azcam

pause
