reg add HKLM\SYSTEM\CurrentControlSet\Services\W32Time\TimeProviders\NtpClient /v SpecialPollInterval /t reg_dword /d 64 /f
reg add HKLM\SYSTEM\CurrentControlSet\Services\W32Time\Config /v MinPollInterval /t reg_dword /d 7 /f
reg add HKLM\SYSTEM\CurrentControlSet\Services\W32Time\Config /v MaxPollInterval /t reg_dword /d 7 /f

w32tm /config /manualpeerlist:"140.252.86.114,0x1 128.196.208.118,0x1 0.pool.ntp.arizona.edu,0x1 0.pool.ntp.org,0x1 tick.usno.navy.mil,0x1 time-b.nist.govtime-b.nist.gov,0x1" /syncfromflags:MANUAL /reliable:NO /update

w32tm /config /update

net stop w32time
net start w32time
w32tm /resync /rediscover
