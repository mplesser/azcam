@echo off

rmdir _build /s /q

:: call C:\data\codevenvs\azcam\Scripts\activate.bat

make html
