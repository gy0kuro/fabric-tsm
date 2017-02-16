@ECHO OFF

SET PASSWORD=tsma42bluz
SET LOGSTAMP=%DATE:/=-%
SET TSMADMIN=admin
SET TSMPWDADMIN=tsm5
SET NODENAME=%COMPUTERNAME%

ECHO Installation : Visual C++ Redistributable
start /wait vcredist_x64.exe /q /c:"msiexec /i vcredist.msi /qn /l*v vcredist_x86.log"

ECHO Creation repertoire tsm
start /wait md c:\tsm
start /wait echo. > c:\tsm\postsched.bat
start /wait echo. > c:\tsm\presched.bat

ECHO Installation : client TSM
start /wait msiexec /i "C:\tmp\IBM Tivoli Storage Manager Client.msi" RebootYesNo="No" REBOOT="Suppress" ALLUSERS=1 INSTALLDIR="c:\program files\tivoli\tsm" ADDLOCAL="BackupArchiveGUI,BackupArchiveWeb,Api64Runtime,AdministrativeCmd" TRANSFORMS=1036.mst /qn /l*v "c:\tmp\InstallTsmClient_%LOGSTAMP%.log"

ECHO Firewall : ouverture des ports
start /wait netsh advfirewall firewall add rule name="TSM Server port OUT" dir=out action=allow protocol=TCP remoteip=172.30.186.3 remoteport=1500
start /wait netsh advfirewall firewall add rule name="TSM Server port IN" dir=in action=allow protocol=TCP remoteip=172.30.186.3 remoteport=1500
start /wait netsh advfirewall firewall add rule name="TSM client Acceptor : dsmcad IN" dir=in action=allow protocol=TCP localport=1552
start /wait netsh advfirewall firewall add rule name="TSM client Acceptor : dsmcad OUT" dir=out action=allow protocol=TCP remoteport=1552
start /wait netsh advfirewall firewall add rule name="TSM Remote Client : dsmagent IN" dir=in action=allow protocol=TCP localport=1553
start /wait netsh advfirewall firewall add rule name="TSM Remote Client : dsmagent OUT" dir=out action=allow protocol=TCP localport=1553
start /wait netsh advfirewall firewall add rule name="TSM Web Client IN" dir=in action=allow protocol=TCP localport=1581
start /wait netsh advfirewall firewall add rule name="TSM Web Client OUT" dir=out action=allow protocol=TCP localport=1581

ECHO Configuration : MAJ et copie du dsm.opt
C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -Command "Get-Content c:\tmp\dsm.opt | %{$_ -replace \"xxx\", \"%COMPUTERNAME%\"} | Set-Content c:\tmp\dsm.opt.new"
XCOPY "c:\tmp\dsm.opt.new" "C:\Program Files\Tivoli\TSM\baclient\dsm.opt" /y

ECHO TSM SRV : Reg node et inscription au planning de sauvegarde
CD /D "C:\program files\tivoli\tsm\baclient"
dsmadmc.exe -id=%TSMADMIN% -pa=%TSMPWDADMIN% "reg node %COMPUTERNAME% %PASSWORD%"
dsmadmc.exe -id=%TSMADMIN% -pa=%TSMPWDADMIN% "upd node %COMPUTERNAME% do=do_srv clo=windows"
dsmadmc.exe -id=%TSMADMIN% -pa=%TSMPWDADMIN% "def assoc do_srv inc_20h00 %COMPUTERNAME%"

ECHO Services : creation
cd "c:\program files\tivoli\TSM\baclient\"
start /wait dsmcutil.exe install cad /name:"TSM Client Acceptor" /optfile:"C:\Program Files\Tivoli\tsm\baclient\dsm.opt" /password:%PASSWORD% /autostart:yes
start /wait dsmcutil.exe install remoteagent /name:"TSM Remote Client Agent" /optfile:"C:\Program Files\Tivoli\tsm\baclient\dsm.opt" /password:%PASSWORD% /clusternode:no
start /wait dsmcutil.exe install scheduler /name:"TSM Scheduler" /clientdir:"C:\Program Files\Tivoli\tsm\baclient" /optfile:"C:\Program Files\Tivoli\TSM\baclient\dsm.opt" /password:%PASSWORD% /validate:yes /autostart:no /startnow:no /clusternode:no
start /wait dsmcutil.exe update cad /name:"TSM Client Acceptor" /cadschedname:"TSM Scheduler"
start /wait dsmc.exe set password %PASSWORD% %PASSWORD%

ECHO Services : Lancement Client Acceptor
NET STOP "TSM Client Acceptor" /Y
NET START "TSM Client Acceptor"

pause
