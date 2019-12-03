# -*- coding: utf-8 -*-

import os
import util

from os import path
from os.path import join
from subprocess import call

def show_diffs_from_initial(backend, config):
	"""
	Pokreće vizuelni diff alat kako bi se prikazale razlike između trenutnog zadatka i postavke zadatka

	backend - back-end koji se trenutno koristi
	config - globalna konfiguracija alata za pregled
	"""
	initfiles = [f for f in os.listdir(config.INITIAL_PROJECT_PATH)
				 if path.isfile(join(config.INITIAL_PROJECT_PATH, f))]
	if len(initfiles) == 0:
		util.fatal_error('U folder "{0}" potrebno je kopirati fajlove koji cine postavku zadatka!'
						 .format(config.INITIAL_PROJECT_PATH))

	print 'Uporedjivanje fajlova zadatka sa pocetnim verzijama fajlova...'
	onlyfiles = [f for f in os.listdir(config.CURRENT_ASSIGNMENT_PATH)
				 if path.isfile(join(config.CURRENT_ASSIGNMENT_PATH, f))]
	found = False
	for f in onlyfiles:
		init = join(config.INITIAL_PROJECT_PATH, f)
		if not util.filename_matches(f, backend.get_ignore_files_pattern()):
			if not path.isfile(init):
				init = '/dev/null'
			student = join(config.CURRENT_ASSIGNMENT_PATH, f)
			if (init == '/dev/null' or (not util.cmp_files_ignore_newlines(init, student))):
				found = True
				command = config.VISUAL_DIFF_CMD.format(init, student)
				ret = call(command, shell=True)
				if ret != 0:
					util.fatal_error('''Pokretanje vizuelnog diff alata nije uspelo!
Komanda koja je pokrenuta:\n{0}'''.format(command))
	if not found:
		print 'Trenutno nema razlika izmedju studentskog zadatka i pocetne verzije!'


def show_diffs_from_student(backend, config):
	"""
	Pokreće vizuelni diff alat kako bi se prikazale razlike između izmenjenog zadatka (alternativne verzije) i zadatka
	onako kako ga je student uradio

	backend - back-end koji se trenutno koristi
	config - globalna konfiguracija alata za pregled
	"""
	print 'Uporedjivanje fajlova prepravljenog zadatka sa verzijama fajlova koje je ostavio student...'

	# Biće pretraženi alt i current direktorijumi i biće pokrenut vizuelni diff za fajlove koji se razlikuju:
	onlyfiles = [f for f in os.listdir(config.CURRENT_ALT_ASSIGNMENT_PATH)
				 if path.isfile(join(config.CURRENT_ALT_ASSIGNMENT_PATH, f))]
	found = False
	for f in onlyfiles:
		alt = join(config.CURRENT_ALT_ASSIGNMENT_PATH, f)
		student = join(config.CURRENT_ASSIGNMENT_PATH, f)
		# Diff se vrši samo ako isti fajl postoji i u config.CURRENT_ASSIGNMENT_PATH direktorijumu:
		if path.isfile(student) and not util.filename_matches(f, backend.get_ignore_files_pattern()):
			if not util.cmp_files_ignore_newlines(alt, student):
				found = True
				command = config.VISUAL_DIFF_CMD.format(student, alt)
				ret = call(command, shell=True)
				if ret != 0:
					util.fatal_error('''Pokretanje vizuelnog diff alata nije uspelo!
Komanda koja je pokrenuta:\n{0}'''.format(command))
	if not found:
		print 'Trenutno nema razlika izmedju prepravljenog zadatka i studentske verzije!'