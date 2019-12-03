# -*- coding: utf-8 -*-

import logging
import util
import os
import os.path as path

from os.path import basename
from util import bcolors
from os.path import join
from shutil import copyfile

def open_assignment(backend, config, station):
	"""
	Otvara pojedinačan studentski zadatak na osnovu zadatog naziva računara na kojem je urađen zadatak

	Zadatak se kopira na putanju config.CURRENT_ASSIGNMENT_PATH, trenutno selektovan računar se menja na zadati.
	Nakon toga poziva se metoda backend.after_assignment_loaded() koja dozvoljava dodatne akcije nakon otvaranja
	zadatka.

	config - globalna konfiguracija alata za pregled
	station - oznaka računara na kojem je zadatak urađen
	"""
	print 'Otvaranje studentskog zadatka sa racunara {0}...'.format(station)
	logging.info('Otvaranje studentskog zadatka sa racunara: {0}'.format(station))

	start_dir = join(config.ASSIGNMENTS_PATH, station)
	matches = backend.find_project_recursive(start_dir)

	if len(matches) == 0:
		print bcolors.FAIL \
              + 'U direktorijumu "{0}" nije pronadjen fajl za identifikaciju projekta (pattern: "{1}")!'\
                  .format(start_dir, backend.get_project_pattern()) + bcolors.ENDC
		return False
	if len(matches) > 1:
		print bcolors.FAIL \
              + 'U direktorijumu "{0}" pronadjeno je vise direktorijuma kandidata za projektni direktorijum: {1}!'\
                  .format(start_dir, matches) + bcolors.ENDC
		return False

	util.clear_directory(config.CURRENT_ASSIGNMENT_PATH)
	util.clear_directory(config.CURRENT_ALT_ASSIGNMENT_PATH)

	onlyfiles = [f for f in os.listdir(matches[0]) if path.isfile(join(matches[0], f))]
	for file in onlyfiles:
		src = join(matches[0], file)
		dst = join(config.CURRENT_ASSIGNMENT_PATH, os.path.basename(file))
		copyfile(src, dst)

	alt = join(config.ALTERED_ASSIGNMENTS_PATH, station)
	if path.isdir(alt):
		print bcolors.BOLD + 'Postoji i izmenjeno resenje ovog zadatka, pa se ono kopira u: "{0}"'\
            .format(config.CURRENT_ALT_ASSIGNMENT_PATH) + bcolors.ENDC
		onlyfiles = [f for f in os.listdir(alt) if path.isfile(join(alt, f))]
		for file in onlyfiles:
			src = join(alt, file)
			dst = join(config.CURRENT_ALT_ASSIGNMENT_PATH, os.path.basename(file))
			copyfile(src, dst)

	write_current_station(config, station)

	proj = basename(util.identify_project_file(backend, config.CURRENT_ASSIGNMENT_PATH))
	print('Identifikovani projektni fajl: {0}'.format(proj))
	try:
		backend.after_assignment_loaded(config.CURRENT_ASSIGNMENT_PATH, proj)
	except RuntimeError as err:
		util.fatal_error(err.message)


def close_current_assignment(config, current_station):
	"""
	Zatvara trenutno otvoreni studentski zadatak

	config - globalna konfiguracija alata za pregled
	current_station - oznaka trenutno selektovanog računara
	"""
	print 'Zatvaranje studentskog zadatka {0}, posto se prelazi na drugi...'.format(current_station)

	onlyfiles = [f for f in os.listdir(config.CURRENT_ALT_ASSIGNMENT_PATH)
                 if path.isfile(join(config.CURRENT_ALT_ASSIGNMENT_PATH, f))]
	if len(onlyfiles) > 0:
		print('Postoji alternativna verzija zadatka, pa se ona kopira u {0}'.format(config.ALTERED_ASSIGNMENTS_PATH))

		altered = join(config.ALTERED_ASSIGNMENTS_PATH, current_station)
		util.make_sure_path_exists(altered)

		logging.info('Detektovano je da postoji alternativna varijanta zadatka, koja je kopirana u: {0}'
                     .format(altered))

		print('Kopiranje fajlova iz "{0}" u "{1}"'.format(config.CURRENT_ALT_ASSIGNMENT_PATH, altered))
		for f in onlyfiles:
			copyfile(join(config.CURRENT_ALT_ASSIGNMENT_PATH, f), join(altered, f))


def copy_assignment_to_alt(config):
	"""
	Kopira trenutni zadatak (u svom trenutnom stanju na kojem može biti izmena) u config.CURRENT_ALT_ASSIGNMENT_PATH -
	putanju sa koje će se zadatak pohraniti u repozitorijum alternativnih verzija zadatka

	Praktično proglašava trenutne izmene na zadatku zvaničnim, beleži ih kao izmene koje je pregledač napravio na
	zadatku.

	config - globalna konfiguracija alata za pregled
	"""
	print 'Pravljenje kopije zadatka u direktorijum za prepravke: "{0}"'.format(config.CURRENT_ALT_ASSIGNMENT_PATH)
	logging.info('Inicirano je pravljenje kopije zadatka radi izrade alternativne varijante')

	util.clear_directory(config.CURRENT_ALT_ASSIGNMENT_PATH)

	onlyfiles = [f for f in os.listdir(config.CURRENT_ASSIGNMENT_PATH)
                 if path.isfile(join(config.CURRENT_ASSIGNMENT_PATH, f))]
	for file in onlyfiles:
		src = join(config.CURRENT_ASSIGNMENT_PATH, file)
		dst = join(config.CURRENT_ALT_ASSIGNMENT_PATH, file)
		copyfile(src, dst)


def read_current_station(config):
	"""
	Vraća oznaku trenutno selektovanog računara

	Ukoliko nema trenutno selektovanog računara, vraća prazan string.

	config - globalna konfiguracija alata za pregled
	"""
	if path.isfile(config.STATION_FILENAME):
		with open (config.STATION_FILENAME, 'r') as rfile:
			return rfile.read()
	else:
		return ''


def write_current_station(config, station):
	"""
	Upisuje oznaku trenutno selektovanog računara u fajl u kojem se evidentira ta informacija

	config - globalna konfiguracija alata za pregled
	station - oznaka trenutno selektovanog računara
	"""
	with open (config.STATION_FILENAME, 'w') as wfile:
		wfile.write(station)