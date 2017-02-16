##
# Script installation client / ddc 11032011 / ddm 13052015.4
# thomas.gratton@ac-amiens.fr
##
# Fonctions disponibles :
#   * installation client TSM v7 et tests operationnels
#   * desinstallation client TSM v7
#   * lancement de backup interactif
#	* recuperation des informations des machines vers csv
#
##  TODO :
#   * messages de notification des differentes etapes ?
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

import fabric.contrib.files
import os.path
from fabric.api import *
#from fabric.contrib.files import append
from fabric.colors import *
import commands

env.user="root"

# env.port="3002"

# LISTE DU OU DES NOEUDS A INSTALLER - IP, shortname, FQDN...
env.roledefs['newnode'] = ['194.254.103.117:3002']


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
            rpms_path = '/home/tom/.bin/DSIN-AMS/TSM/rpms/'
            # path paquets Debian
            debs_path = '/home/tom/.bin/DSIN-AMS/TSM/deb/'
            # path paquets Debian officiels (best effort)
            #debs_path = '/home/tom/.bin/DSIN-AMS/TSM/deb/official_release/'
            # votre path temporaire
            tmp_path = '/tmp/tsm/'
            # path arbo client TSM si different de install de base
            tsmclient_path = '/opt/tivoli/tsm/client/'
            # adresse serveur TSM
            tsmsrvaddress = '194.254.103.30'
            # utilisateur TSM pour enregistrer le noeud
            tsmuser = 'adminpeda1'
            # TODOLIST : trouver la librairie pour crypter et decrypter les mdp
            # password utilisateur TSM
            tsmsrvpwd = 'a42bluz'
            # password noeud
            tsmclipwd = 'a42bluz'
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
                    run('rpm -ivh '+tmp_path+'*')
                    #if ()
                    # FAIRE UN TEST DE RETOUR ERREUR OU NON
                    run('chkconfig dsmcad on')

                elif fabric.contrib.files.exists('/etc/issue'):
                    put(''+debs_path+'*.deb',''+tmp_path+'')
                    run('dpkg -i '+tmp_path+'*.deb')
                    #if ()
                    # FAIRE UN TEST DE RETOUR ERREUR OU NON
                    put(''+debs_path+'dsmcad.debian','/etc/init.d/dsmcad')
                    run('chmod 755 /etc/init.d/dsmcad')
                    run('update-rc.d dsmcad defaults && update-rc.d dsmcad enable')
                    run('cd /opt/tivoli/tsm/client/ba/bin/')
                    run('ln -s ../../lang/FR_FR/ FR_FR')
                    # AJOUT LIGNES QUI VONT BIEN /etc/ld.so.conf.d/tsm.conf
                    run('echo "# TSM - configuration par defaut" > /etc/ld.so.conf.d/tsm.conf')
                    run('echo "'+tsmclient_path+'api/bin64/" >> /etc/ld.so.conf.d/tsm.conf')
                    run('echo "/usr/local/ibm/gsk8_64/lib64/" >> /etc/ld.so.conf.d/tsm.conf')
                    run('ldconfig')
                else:
                    print('??? WTF : ni DEB ni RHEL ???')
                    run('exit')

                # LDCONFIG

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
                run('/etc/init.d/dsmcad restart')

                # TEST A ALLEGER AVEC UN SWITCH ?
                # TEST DEMON LANCE
                myoutput = run('ps -A |grep dsmcad |grep -v grep')

                # TESTS RESEAUX
                mysrvport = run('nc -v -z -w 1 '+tsmsrvaddress+' 1500')
                myclientport = run('nc -v -z -w 1 '+hostname+' 1581')
                
                # TEST TOUT EST OK
                if 'dsmcad' in myoutput and 'succeeded' in mysrvport and 'succeeded' in myclientport:
                    print (green("demon dsmcad : OK"))
                    print (green("port serveur : UP"))
                    print (green("port client : UP"))
                    print (green("simulation scheduled backup"))
                    run('dsmadmc -id='+tsmuser+' -password='+tsmsrvpwd+' "def clienta '+hostname_short+' action=inc"')

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

                # SUPPRESSION PAQUETS
                run('rm -Rf '+tmp_path+'')

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
            #run('dsmadmc -id=admin -password=tsm5 "remove node '+hostname+'"')

            #if fabric.contrib.files.exists('/opt/tivoli/tsm/client/ba/bin/dsm.sys'):
            if fabric.contrib.files.exists('/etc/redhat-release'):
                TIVBA = run('rpm -qa |grep TIVsm-BA')
                TIVAPI = run('rpm -qa |grep TIVsm-API')
                TIVMSG = run('rpm -qa |grep TIVsm-msg')
                GSKCRYPT = run('rpm -qa | grep gskcrypt')
                GSKSSL = run('rpm -qa | grep gskssl')
                run('rpm -e '+TIVBA+'')
                run('rpm -e '+TIVAPI+'')
                run('rpm -e '+TIVMSG+'')
                run('rpm -e '+GSKCRYPT+'')
                run('rpm -e '+GSKSSL+'')

            elif fabric.contrib.files.exists('/etc/issue'):
                run('dpkg -r gskcrypt64 gskssl64 && dpkg -r tivsm-api64 tivsm-ba tivsm-msg.fr-fr')
                run('dpkg --purge gskcrypt64 gskssl64 tivsm-api64 tivsm-ba tivsm-msg.fr-fr')
                run('rm -f /etc/ld.so.conf.d/tsm.conf')
                run('update-rc.d dsmcad remove')

            if fabric.contrib.files.exists('/opt/tivoli/'):
                print(green("suppression /opt/tivoli"))
                run('rm -Rf /opt/tivoli')
            if fabric.contrib.files.exists('/etc/init.d/dsmcad'):
                print(green("suppression /etc/init.d/dsmcad"))
                run('rm -f /etc/init.d/dsmcad')
            else:
                run('exit')


#
# DSMCBACKUP INTERACTIF
#

@roles('')

def dsmcbackup():

        # bailloner output
        with settings(
        hide('warnings', 'running', 'stderr','stdout'),
        warn_only=True
        ):

		output = run('/usr/bin/dsmc backup')
		rc = output.return_code

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
# OK pour RHEL a tester pour Debian likes

csvio='output.csv'

@roles('')

def grabinfos():

        print(green(" Collecte d\'infos "))

        with settings(
        hide('warnings', 'running', 'stderr','stdout'),
        warn_only=True
        ):

                target = open(csvio, 'a')

                hostname = run('/bin/hostname -s')
                kernel = run('/bin/uname -r')
                release = run('/bin/cat /etc/issue | cut -b 26-55')
                version = run('/bin/arch')
                vm = run ('lspci 2>|/dev/null | grep -i vmware | cut -b 20-26')
                tsmcliver = run('/bin/rpm -qa | grep TIV | grep BA | cut -b 10-16')
                gskcrypt = run('/bin/rpm -qa | grep gskcrypt64 | cut -b 12-16')
                gskssl = run('/bin/rpm -qa | grep gskssl64 | cut -b 12-17')

                target.write("\n")
                target.write(hostname+";"+kernel+";"+release+";"+version+";"+vm+";"+tsmcliver+";"+gskcrypt+";"+gskssl)

        target.close()
