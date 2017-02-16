#!/usr/bin/env python

#
#	Documentation
#	https://docs.python.org/2/howto/curses.html
#	http://tuxradar.com/content/code-project-build-ncurses-ui-python#null
#	http://urwid.org/examples/index.html#
#	http://pycdk.sourceforge.net/


from os import system
import curses

def get_param(prompt_string):
	screen.clear()
	screen.border(0)
	screen.addstr(2, 2, prompt_string)
	screen.refresh()
	input = screen.getstr(10, 10, 60)
	return input

def execute_cmd(cmd_string):
	system("clear")
	a = system(cmd_string)
	print ""
	if a == 0:
		print "Commande executee correctement"
	else:
		print "Erreur, bonne chance !"
	raw_input("Press enter")
	print ""

x = 0

while x != ord('4'):
	screen = curses.initscr()

	screen.clear()
	screen.border(0)
	screen.addstr(2, 2, "Client TSM Linux")
	screen.addstr(4, 4, "1 - Installation du client")
	screen.addstr(5, 4, "2 - Suppression du client")
	screen.addstr(6, 4, "3 - Backup interactif du client")
	screen.addstr(7, 4, "4 - Exit")
	screen.refresh()

	x = screen.getch()

	if x == ord('1'):
		hostname = get_param("Saisir le nom (pas FQDN) ou l'IP de(s) la machine(s) separes par des virgules")
		#parallelise = get_param("Execution en parallele ?")
		curses.endwin()
		execute_cmd("fab client_tsm_install -f tsm_tools.py -h" +hostname)
	if x == ord('2'):
		hostname = get_param("Saisir le nom (pas FQDN) ou l'IP de(s) la machine(s) separes par des virgules")
		#parallelise = get_param("Execution en parallele ?")
		curses.endwin()
		execute_cmd("fab client_tsm_uninstall -f tsm_tools.py -h" +hostname)
	if x == ord('3'):
		curses.endwin()
		execute_cmd("df -h")

curses.endwin()
