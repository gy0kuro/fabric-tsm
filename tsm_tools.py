#!/usr/bin/python
##
# Script installation client / ddc tgr.11032011 / ddm tgr.09022017.1
##
# Fonctions disponibles :
#   * installation client TSM v7 et tests operationnels
#   * desinstallation client TSM v7
#   * lancement de backup interactif
#	* recuperation des informations des machines vers csv
#
##  TODO :
#   * gestion installation specifique db2
#   * alleger les tests operationnels avec equivalent du switch/case qui n existe pas en python
##
#
# Documentation :
#
#	http://learnpythonthehardway.org/book/ex16.html
#	http://learnpythonthehardway.org/book/ex5.html
#	http://api.mongodb.org/python/
#	http://fabric.readthedocs.org/en/1.3.3/api/core/colors.html#module-fabric.colors
##
# fab <fonction> <facultatif : -P -z <nombre instances en parallele> - option P seule conseillee> -f matice_systools.py
#
# diffusion de clefs
# run('sshpass -f password.txt ssh-copy-id root@yourserver')
# sshpass -p 'motdepasse' ssh -o StrictHostKeyChecking=no username@server.example.com


import fabric.contrib.files
import os.path
from fabric.api import *
#from fabric.contrib.files import append
from fabric.colors import *
import commands


import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

# Parametres mail

#fromaddr = "tsmclientop@yourcompany.com"
#toaddr = "system@yourcompany.com"
#msg = MIMEMultipart()
#msg['From'] = fromaddr
#msg['To'] = toaddr
#msg['Subject'] = "TSM client OP"
#
#body = env.roledefs['newnode']
#msg.attach(MIMEText(body, 'plain'))
#
#server = smtplib.SMTP('smtp.yourcompany.com', 587)
#server.starttls()
#server.login(fromaddr, "YOUR PASSWORD")
#text = msg.as_string()

# fin parametres mail

env.user="root"

env.skip_bad_hosts=True
env.skip_unknown_tasks=True
env.abort_on_prompts=True

# LISTE DU OU DES NOEUDS A INSTALLER - IP, shortname, FQDN...

env.roledefs['newnode'] = ['server.yourcompany.com']

# INSTALL CLIENT 7

@roles('newnode')

def tsm_client_install():

        with settings(
        hide('stderr','stdout'),
        warn_only=True
        ):

            #
            # VARIABLES A PERSONNALISER
            #
            # path paquets RHEL
            rpms_path = '/home/tonuser/pathto/rpms/'
            # path paquets Debian
            debs_path = '/home/tonuser/pathto/deb/'
            # votre path temporaire
            tmp_path = '/tmp/tsm/'
            # path arbo client TSM si different de install de base
            tsmclient_path = '/opt/tivoli/tsm/client/'
            # adresse serveur TSM
            tsmsrvaddress = 'IP'
            # utilisateur TSM pour enregistrer le noeud
            tsmuser = 'USER'
            # TODOLIST : trouver la librairie pour crypter et decrypter les mdp
            # password utilisateur TSM
            tsmsrvpwd = 'PASSWORD'
            # password noeud
            tsmclipwd = 'NODE PASSWORD'
            #

            if fabric.contrib.files.exists(''+tsmclient_path+'ba/bin/dsm.sys'):
                if fabric.contrib.files.exists('/etc/redhat-release'):
                    versioncli = run('rpm -qa |grep TIV |grep BA | cut -b 10-20')
                    print(red('client '+versioncli+' present'))
                    run('exit')
                if fabric.contrib.files.exists('/etc/issue'):
                    versioncli = run('dpkg -s tivsm-ba |grep Version | cut -b 10-20')
                    print(red('client '+versioncli+' present'))
                    run('exit')
            else:
                # path temp des paquets
                run('mkdir '+tmp_path+'')

                # INSTALLATION
                if fabric.contrib.files.exists('/etc/redhat-release'):
                    run('yum install -y nc')
                    put(''+rpms_path+'*.rpm',''+tmp_path+'')
                    run('rpm -ivh '+tmp_path+'*.rpm')
                    # FAIRE UN TEST DE RETOUR ERREUR OU NON
                    put('/home/tom/.bin/DSIN-AMS/TSM/dsmcad.service','/etc/systemd/system/')
                    run('chmod a+x /etc/systemd/system/dsmcad.service')

                elif fabric.contrib.files.exists('/etc/issue'):
                    # INSTALL PACKAGES
                    put(''+debs_path+'*.deb',''+tmp_path+'')
                    run('chmod 777 '+tmp_path+'*')
                    run('cd '+tmp_path+'')
                    run('/usr/bin/dpkg -i gskcrypt64_8.0-50.66.linux.x86_64.deb')
                    run('/usr/bin/dpkg -i gskssl64_8.0-50.66.linux.x86_64.deb')
                    run('/usr/bin/dpkg -i tivsm-api64.amd64.deb')
                    run('/usr/bin/dpkg -i tivsm-ba.amd64.deb')
                    # CONF SYSTEMD
                    put('/home/tom/.bin/DSIN-AMS/TSM/dsmcad.service','/etc/systemd/system/')
                    run('chmod a+x /etc/systemd/system/dsmcad.service')

                else:
                    print (red("??? WTF : ni DEB ni RHEL ???"))
                    run('exit')

                # CREATION PRE ET POSTSCHED
                run('mkdir /tsm && touch /tsm/postsched.sh && touch /tsm/presched.sh && chmod 755 /tsm/postsched.sh && chmod 755 /tsm/presched.sh')

                # REMPLACEMENT DSM.SYS/OPT
                ################# TODOLIST DB2
                run('rm -f '+tsmclient_path+'ba/bin/dsm.opt.smp && rm -f '+tsmclient_path+'ba/bin/dsm.sys.smp')
                put('/home/tom/.bin/DSIN-AMS/TSM/dsm.*','/opt/tivoli/tsm/client/ba/bin/')
                run('chmod 755 '+tsmclient_path+'ba/bin/dsm.sys')
                run('chmod 755 '+tsmclient_path+'ba/bin/dsm.opt')
                hostname = run('/bin/hostname -f')
                hostname_short = run('/bin/hostname -s')
                run('sed -i -e "s/xxx/'+hostname+'/g" '+tsmclient_path+'ba/bin/dsm.sys')
                run('sed -i -e "s/yyy/'+hostname_short+'/g" '+tsmclient_path+'ba/bin/dsm.sys')

                # ENREGISTREMENT NODE
                ################# TODOLIST DB2
                run('dsmadmc -id='+tsmuser+' -password='+tsmsrvpwd+' "reg node '+hostname_short+' '+tsmclipwd+'"')
                run('dsmadmc -id='+tsmuser+' -password='+tsmsrvpwd+' "upd no '+hostname_short+' do=do_srv clo=linux"')
                run('dsmadmc -id='+tsmuser+' -password='+tsmsrvpwd+' "def assoc do_srv inc_20h00 '+hostname_short+'"')

                # REGISTER DSMC
                run('dsmc set password '+tsmclipwd+' '+tsmclipwd+'')
                run('quit')

                # REDEMARRAGE CLIENT
                run('systemctl start dsmcad.service')
                run('systemctl enable dsmcad.service')
                run('systemctl daemon-reload')


                # TEST DEMON LANCE
                myoutput = run('ps -A |grep dsmcad |grep -v grep')

                # TESTS RESEAUX
                mysrvport = run('nc -v -z -w 1 '+tsmsrvaddress+' 1500')
                myclientport = run('nc -v -z -w 1 '+hostname+' 1581')

                # TEST A ALLEGER : AVEC UN SWITCH ?
                # TEST TOUT EST OK
                if 'dsmcad' in myoutput and 'succeeded' in mysrvport and 'succeeded' in myclientport:
                    print (green("demon dsmcad : OK"))
                    print (green("port serveur : UP"))
                    print (green("port client : UP"))
                    print (blue("Simulation scheduled backup ..."))
                    run('dsmadmc -id='+tsmuser+' -password='+tsmsrvpwd+' "def clienta '+hostname_short+' action=inc"')
                    # ENVOI DUN EMAIL DE NOTIF
                    #server.sendmail(fromaddr, toaddr, text)
                    #server.quit()

                # TEST DSMCAD OK PORT SERVEUR OK PORT CLIENT PAS OK
                elif 'dsmcad' in myoutput and 'succeeded' in mysrvport and 'succeeded' not in myclientport:
                    print (green("demon dsmcad : OK"))
                    print (green("port serveur : UP"))
                    print (red("port client : INJOIGNABLE"))
                # TEST DSMCAD OK PORT SERVEUR PAS OK
                elif 'dsmcad' in myoutput and 'succeeded' not in mysrvport and 'succeeded' in myclientport:
                    print (green("demon dsmcad : OK"))
                    print (red("port serveur : INJOIGNABLE"))
                    print (green("port client : UP"))
                # TEST DSMCAD DOWN
                elif 'dsmcad' not in myoutput and 'succeeded' in mysrvport and 'succeeded' in myclientport:
                    print (red("dsmcad : DOWN"))
                    print (green("port serveur : UP"))
                    print (green("port client : UP"))

            run('exit')
       

# DESINSTALLATION CLIENT 7

@roles('newnode')

def tsm_client_uninstall():

        with settings(
        hide( 'stderr','stdout'),#'warnings', 'running',
        warn_only=True
        ):

            myoutput = run('ps -A |grep dsmcad |grep -v grep')
            if 'dsmcad' in output:
                run('killall dsmcad')
                print "Client OK"
            else:
                print(red("daemon absent"))

            if fabric.contrib.files.exists('/tsm'):
                print(green("suppression /tsm"))
                run('rm -Rf /tsm')
                run('rm -f /etc/systemd/system/dsmcad.service')

            if fabric.contrib.files.exists('/opt/tivoli/tsm/client/ba/bin/dsm.sys'):
                if fabric.contrib.files.exists('/etc/redhat-release'):
                    TIVBA = run('rpm -qa |grep TIVsm-BA')
                    TIVAPI = run('rpm -qa |grep TIVsm-API')
                    GSKCRYPT = run('rpm -qa | grep gskcrypt')
                    GSKSSL = run('rpm -qa | grep gskssl')
                    run('rpm -e '+TIVBA+'')
                    run('rpm -e '+TIVAPI+'')
                    run('rpm -e '+TIVMSG+'')
                    run('rpm -e '+GSKCRYPT+'')
                    run('rpm -e '+GSKSSL+'')

                else:
                    # elif fabric.contrib.files.exists('/etc/issue'):
                    run('dpkg -r gskcrypt64 gskssl64 && dpkg -r tivsm-api64 tivsm-ba')
                    run('dpkg --purge gskcrypt64 gskssl64 tivsm-api64 tivsm-ba')
                    run('rm -f /etc/ld.so.conf.d/tsm.conf')
                    run('update-rc.d dsmcad remove')

            if fabric.contrib.files.exists('/opt/tivoli/'):
                print(green("suppression /opt/tivoli"))
                run('cd /opt/')
                run('rm -Rf tivoli/')

            if fabric.contrib.files.exists('/etc/init.d/dsmcad'):
                print(green("suppression /etc/init.d/dsmcad"))
                run('rm -f /etc/init.d/dsmcad')

            else:
                run('exit')


#
# DSMCBACKUP INTERACTIF
#


@roles('backupinteractif')

def dsmcbackup():

        # bailloner output
        with settings(
        hide('warnings', 'running', 'stderr','stdout'),
        warn_only=True
        ):

		output = run('/usr/bin/dsmc backup')
		rc = output.return_code

        # messages en angliche
		if rc == 0:
			print(green("All operations successfull"))
		elif rc == 4:
			print(yellow("The operation completed successfully, but some files were not processed."))
		elif rc == 8:
			print(magenta("At list one warning, please see logs"))
		elif rc == 12:
			print(red("Failure"))
		else:
			print(blue("Use the logs Luke"))


#
# FONCTION DE COLLECTE DE DONNEES
#

csvio='output.csv'

@roles('pool1')

def grabinfos():

        compteur = 0
        print(green(" Collecte d\'infos "))

        with settings(
        hide('stdout'),
        warn_only=True
        ):

                #compteur = compteur + 1

                target = open(csvio, 'a')

                hostname = run('hostname -s')
                hostip = run('ifconfig -a |grep eth0 -A1 |grep "inet adr" |cut -b 20-34')
                kernel = run('uname -r')
                
                # test VM a faire
                # vm = run ('lspci 2>|/dev/null | grep -i vmware | cut -b 20-26')

                if fabric.contrib.files.exists('/etc/redhat-release'):
                    release = run('cat /etc/redhat-release | cut -b 26-55')
                    tsmcliver = run('rpm -qa | grep TIV | grep BA | cut -b 10-16')
                    version = run('arch')             
                else:
                    release = run('cat /etc/issue')
                    tsmcliver = run('dpkg -l | grep -i tivsm | grep -i ba | cut -b 43-50')
                    version = run('arch')

                target.write("\n")
                target.write(hostname+";"+hostip+";"+kernel+";"+release+";"+version+";"+tsmcliver)

                # compteur a faire
                #print ("serveurs traites." % compteur)

        #print(red(compteur2+" en erreur ou injoignables."))
        target.close()
