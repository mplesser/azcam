nssm install xpans c:\SAOImageDS9\xpans.exe
nssm set xpans AppDirectory c:\SAOImageDS9\
nssm set xpans Start SERVICE_AUTO_START
nssm set xpans Description xpans service for ds9
nssm start xpans
