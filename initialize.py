# -*- coding: utf-8 -*-

import os
import sys
import util
import logging
import json
import codecs
import glob
import csv
import time

from os.path import basename
from os.path import join
from util import bcolors
from shutil import copyfile
from subprocess import call


def execute_init_command(config, stations, all_backends, log_filename):
	"""
	Izvršavanje komande za inicijalizaciju pregleda (postavljanje materijala i određivanje kriterijuma pregleda)

	config - globalna konfiguracija alata za pregled
	stations - kolekcija računara i studenata koji su radili zadatak (ključ - oznaka računara, podatak - lista - broj
	           indeksa i ime/prezime studenta)
	all_backends - lista instanci klase Backend - sve raspoložive implementacije back-end-a
	"""

	# Pribavljanje sadržaja tekućeg direktorijuma kako bi se proverilo da li je on prazan:
	lista = os.listdir('.')
	# Ako u tekućem direktorijumu postoji log fajl, on se ignoriše:
	lista.remove(log_filename)

	# Tekući direktorijum mora biti prazan da bi se dozvolila inicijalizacija projekta:
	if lista != []:
		print bcolors.FAIL + 'Tekuci direktorijum nije prazan!' + bcolors.ENDC
		print 'Ne moze se inicirati pregled zadataka u ovom direktorijumu.'
		sys.exit(1)

	print 'Inicijalizacija pregleda je pokrenuta, molim pratite instrukcije na ekranu.'

	print 'Izbor predmeta/backend-a za kompajliranje i pokretanje zadataka'
	print 'Alat je trenutno konfigurisan da podrzava sledece varijante backend-a:'

	option = 1
	for b in all_backends:
		print '{0}) Naziv: {1}, Ver: {2}, Opis: {3}'.format(option, b.name(), b.version(), b.description())
		option += 1

	izbor = util.get_option_answer(1, option-1)

	backend = all_backends[izbor-1]

	grupe = util.get_yesno_answer('Da li u ovoj proveri postoje grupe A i B?')
	autotest = util.get_yesno_answer('Da li ce pregled biti obavljen automatizovano?')

	# Kreiranje dva poddirektorijuma za pregled po grupama:
	if grupe:
		util.make_sure_path_exists(config.GROUP1_DIR)
		util.make_sure_path_exists(config.GROUP2_DIR)
		print ''
		print bcolors.OKBLUE + 'Zadaci grupa A i B tretirace se kao dva odvojena zadatka koji se pregledaju.' \
			  + bcolors.ENDC
		print 'Za zadatke grupe A kreiran je direktorijum "{0}" u kojem ce se postaviti fajlovi za pregled.'\
			.format(config.GROUP1_DIR)
		print 'Za zadatke grupe B kreiran je direktorijum "{0}" sa istom svrhom.'.format(config.GROUP2_DIR)
		print ''

	print 'Kopiranje neophodnih fajlova u tekuci direktorijum...'

	# Kopiranje XSLT fajla:
	dir = os.path.dirname(__file__)
	xslt_path = join(dir, config.FINAL_REPORT_XSLT_FILENAME)
	if grupe:
		copyfile(xslt_path, join(config.GROUP1_DIR, config.FINAL_REPORT_XSLT_FILENAME))
		copyfile(xslt_path, join(config.GROUP2_DIR, config.FINAL_REPORT_XSLT_FILENAME))
	else:
		copyfile(xslt_path, join('.', config.FINAL_REPORT_XSLT_FILENAME))


	# Priprema direktorijuma u koje će se raspakovati zadaci:
	if grupe:
		util.make_sure_path_exists(join(config.GROUP1_DIR, config.ASSIGNMENTS_PATH))
		util.make_sure_path_exists(join(config.GROUP2_DIR, config.ASSIGNMENTS_PATH))
	else:
		util.make_sure_path_exists(config.ASSIGNMENTS_PATH)

	util.make_sure_path_exists(config.ARCHIVE_PATH)
	print 'Postaviti sledeci sadrzaj u poddirektorijume:'
	print '\n1) Arhivu sa svim uradjenim zadacima u direktorijum "{0}"'.format(config.ARCHIVE_PATH)
	print 'Naziv arhive treba da bude u formatu: "{0}"'.format(config.ASSIGNMENTS_ARCHIVE_PATTERN)
	wait_until_files_are_set(config.ARCHIVE_PATH)
	unpack_assignments(config, stations, grupe)
	os.rename(config.ARCHIVE_PATH, config.BACKUP_PATH)
	print ''


	# Kopiranje postavke zadatka u odgovarajući direktorijum:
	if grupe:
		group1_initial_path = join(config.GROUP1_DIR, config.INITIAL_PROJECT_PATH)
		util.make_sure_path_exists(group1_initial_path)
		group2_initial_path = join(config.GROUP2_DIR, config.INITIAL_PROJECT_PATH)
		util.make_sure_path_exists(group2_initial_path)

		print '2A) Postavku zadatka grupe A koja je data studentima u direktorijum "{0}"'.format(group1_initial_path)
		wait_until_files_are_set(group1_initial_path)

		print '2B) Postavku zadatka grupe B koja je data studentima u direktorijum "{0}"'.format(group2_initial_path)
		wait_until_files_are_set(group2_initial_path)
	else:
		util.make_sure_path_exists(config.INITIAL_PROJECT_PATH)

		print '2) Postavku zadatka koja je data studentima u direktorijum "{0}"'.format(config.INITIAL_PROJECT_PATH)
		wait_until_files_are_set(config.INITIAL_PROJECT_PATH)
	print ''


	# Kopiranje autotest varijante zadatka u odgovarajući direktorijum:
	if autotest:
		if grupe:
			group1_autotest_path = join(config.GROUP1_DIR, config.AUTOTEST_PATH)
			util.make_sure_path_exists(group1_autotest_path)
			group2_autotest_path = join(config.GROUP2_DIR, config.AUTOTEST_PATH)
			util.make_sure_path_exists(group2_autotest_path)

			print '\n3A) Autotest varijantu zadatka grupe A u direktorijum "{0}"'.format(group1_autotest_path)
			wait_until_files_are_set(group1_autotest_path)

			print '\n3B) Autotest varijantu zadatka grupe B u direktorijum "{0}"'.format(group2_autotest_path)
			wait_until_files_are_set(group2_autotest_path)
		else:
			util.make_sure_path_exists(config.AUTOTEST_PATH)
			print '\n3) Autotest varijantu zadatka u direktorijum "{0}"'.format(config.AUTOTEST_PATH)
			wait_until_files_are_set(config.AUTOTEST_PATH)
		print ''


	# Kreiranje dodatnih poddirektorijuma koji se koriste u pregledu:
	if grupe:
		util.make_sure_path_exists(join(config.GROUP1_DIR, config.ALTERED_ASSIGNMENTS_PATH))
		util.make_sure_path_exists(join(config.GROUP1_DIR, config.CURRENT_ASSIGNMENT_PATH))
		util.make_sure_path_exists(join(config.GROUP1_DIR, config.CURRENT_ALT_ASSIGNMENT_PATH))
		util.make_sure_path_exists(join(config.GROUP1_DIR, config.REPORTS_PATH))
		
		util.make_sure_path_exists(join(config.GROUP2_DIR, config.ALTERED_ASSIGNMENTS_PATH))
		util.make_sure_path_exists(join(config.GROUP2_DIR, config.CURRENT_ASSIGNMENT_PATH))
		util.make_sure_path_exists(join(config.GROUP2_DIR, config.CURRENT_ALT_ASSIGNMENT_PATH))
		util.make_sure_path_exists(join(config.GROUP2_DIR, config.REPORTS_PATH))
	else:
		util.make_sure_path_exists(config.ALTERED_ASSIGNMENTS_PATH)
		util.make_sure_path_exists(config.CURRENT_ASSIGNMENT_PATH)
		util.make_sure_path_exists(config.CURRENT_ALT_ASSIGNMENT_PATH)
		util.make_sure_path_exists(config.REPORTS_PATH)


	# Definisanje kriterijuma za ocenjivanje zadatka.
	# Mora se izvršavati posle postavljanja inicijalne verzije zadatka, jer koristi putanje koje ona definiše.
	if autotest:
		if grupe:
			group1_criteria_path = join(config.GROUP1_DIR, config.RATING_CRITERIA_FILENAME)
			group2_criteria_path = join(config.GROUP2_DIR, config.RATING_CRITERIA_FILENAME)

			raw_input('''U tekst editoru bice otvoren fajl "{0}" u kojem se definise kriterijum za zadatak grupe A.
Pritisnite <ENTER> za nastavak.'''.format(group1_criteria_path))
			generate_empty_criteria_file(backend, group1_criteria_path, group1_initial_path, group1_autotest_path)
			util.show_text_edit(config, group1_criteria_path)
			raw_input('Pritisnite <ENTER> kada ste zavrsili sa izmenama u fajlu...')

			raw_input('''U tekst editoru bice otvoren fajl "{0}" u kojem se definise kriterijum za zadatak grupe A.
Pritisnite <ENTER> za nastavak.'''.format(group2_criteria_path))
			generate_empty_criteria_file(backend, group2_criteria_path, group2_initial_path, group2_autotest_path)
			util.show_text_edit(config, group2_criteria_path)
			raw_input('Pritisnite <ENTER> kada ste zavrsili sa izmenama u fajlu...')
		else:
			raw_input('''U tekst editoru bice otvoren fajl "{0}" u kojem se definise kriterijum (nacin bodovanja).
Pritisnite <ENTER> za nastavak.'''.format(config.RATING_CRITERIA_FILENAME))
			generate_empty_criteria_file(backend, config.RATING_CRITERIA_FILENAME, config.INITIAL_PROJECT_PATH,
										 config.AUTOTEST_PATH)
			util.show_text_edit(config, config.RATING_CRITERIA_FILENAME)
			raw_input('Pritisnite <ENTER> kada ste zavrsili sa izmenama u fajlu...')
		print ''

	print 'Svi materijali su postavljeni na odgovarajuce pozicije, mozete poceti sa pregledom zadataka.'
	sys.exit(0)


def unpack_assignments(config, stations, two_groups):
	"""
	Raspakuje arhivu sa svim studentskim radovima iz direktorijuma config.ARCHIVE_PATH

	config - globalna konfiguracija alata za pregled
	stations - kolekcija računara i studenata koji su radili zadatak (ključ - oznaka računara, podatak - lista - broj
	           indeksa i ime/prezime studenta)
	two_groups - boolean koji indikuje da li je zadatak rađen u dve grupe (A i B)
	"""
	util.make_sure_path_exists(config.TEMP_PATH)

	# Ukoliko se u prihvatnom direktorijumu nalazi arhiva, ona će biti raspakovana u direktorijum sa studentskim
	# zadacima i potom premeštena u backup direktorijum:
	archives = glob.glob(join(config.ARCHIVE_PATH, config.ASSIGNMENTS_ARCHIVE_PATTERN))
	found = 0
	for a in archives:
		found = found + 1
		print 'Pronadjena je nova arhiva sa zadacima koja ce biti obradjena'
		print 'Raspakivanje arhive "{0}" u direktorijum "{1}"...'.format(a, config.TEMP_PATH)
		command = config.EXTRACT_ASSIGNMENTS_CMD.format(a, config.TEMP_PATH)
		ret = call(command, shell=True)
		if ret != 0:
			util.fatal_error('Raspakivanje arhive sa zadacima je neuspesno!\nKomanda koja je pokrenuta:\n{0}'
							 .format(command))

	if found == 0:
		util.fatal_error('''Nije pronadjena arhiva sa zadacima! 
Molim proverite da li arhiva koju ste prilozili ima adekvatan naziv i adekvatnu ekstenziju! 
Ocekuje se naziv poput sledeceg: {0}'''.format(config.ASSIGNMENTS_ARCHIVE_PATTERN))

	# Učitavanje liste studenata iz raspakovanog sadrzaja arhive:
	matches = glob.glob(join(config.TEMP_PATH, config.STUDENTS_LIST_PATTERN))

	if len(matches) == 0:
		util.fatal_error('Nije pronadjena lista studenata (pattern za trazenje: "{0}")'
						 .format(config.STUDENTS_LIST_PATTERN))
	if len(matches) > 1:
		util.fatal_error('Pronadjen je vise od jednog fajla koji je kandidat za listu studenata. Kandidati: {0}'
						 .format(matches))
	
	# Ako zadatak ima samo jednu grupu (nema grupe A i B), onda se lista studenata samo kopira na destinaciju
	# (neće biti njene podele na dve podgrupe):
	if not two_groups:
		copyfile(matches[0], join(config.ASSIGNMENTS_PATH, basename(matches[0])))

	logging.debug('Ucitavanje spiska studenata prilikom raspakivanja arhive...')
	ifile = open(matches[0], "rb")
	reader = csv.DictReader(ifile, dialect='excel', fieldnames=['station', 'id', 'name'])
	for row in reader:
		station = row['station'].strip()
		id = row['id'].strip() 
		name = row['name'].strip()
		if id:
			logging.debug('Ucitano: Stanica: {0}, Broj indeksa: {1}, Ime: {2}'.format(station, id, name))
			stations[station] = [id, name]
	ifile.close()
	logging.debug('Ucitavanje spiska studenata zavrseno')

	if two_groups:
		group1_list = open(join(config.GROUP1_DIR, config.ASSIGNMENTS_PATH,
								"spisak_stud_koji_trenutno_rade_proveru.txt"), "a+")
		group2_list = open(join(config.GROUP2_DIR, config.ASSIGNMENTS_PATH,
								"spisak_stud_koji_trenutno_rade_proveru.txt"), "a+")

	# Arhive koje su pronađene u direktorijumu sa studentskim zadacima biće raspakovane i potom obrisane:
	archives = sorted(glob.glob(join(config.TEMP_PATH, config.SINGLE_ASSIGNMENT_ARCHIVE_PATTERN)))
	for a in archives:
		logging.debug('Pronadjena je sledeca arhiva sa pojedinacnim zadatkom: {0}'.format(a))

		# Manipulacija nazivom arhive, kako bi se došlo do oznake stanice na kojoj je student radio:
		name = os.path.basename(a)[:-len(config.SINGLE_ASSIGNMENT_ARCHIVE_EXT)]
		tokens = name.split('_')
		station = tokens[len(tokens)-1]

		# Proces kopiranja zadataka vođen je spiskom studenata koji su radili proveru.
		# Ako stanica nije na tom spisku, znači da je u pitanju blanko direktorijum i on se preskače.
		if station in stations:
			if two_groups:
				station_num = int(station[1:])
				if station_num % 2 == 0:
					station_directory = join(config.GROUP1_DIR, config.ASSIGNMENTS_PATH, station)
					if not station in stations:
						util.fatal_error(
							'Racunar sa oznakom "{0}" nije pronadjen u spisku studenata koji rade proveru!'
								.format(station))
					group1_list.write('{0}, {1}, {2}\n'.format(station, stations[station][0], stations[station][1]))
				else:				
					station_directory = join(config.GROUP2_DIR, config.ASSIGNMENTS_PATH, station)
					if not station in stations:
						util.fatal_error(
							'Racunar sa oznakom "{0}" nije pronadjen u spisku studenata koji rade proveru!'
								.format(station))
					group2_list.write('{0}, {1}, {2}\n'.format(station, stations[station][0], stations[station][1]))
			else:
				station_directory = join(config.ASSIGNMENTS_PATH, station)

			logging.debug('Raspakivanje zadatka "{0}" u direktorijum "{1}"'.format(a, station_directory))
			util.make_sure_path_exists(station_directory)
			command = config.EXTRACT_SINGLE_ASSIGNMENT_CMD.format(a, station_directory)
			ret = call(command, shell=True)
			if ret != 0:
				util.fatal_error('Raspakivanje pojedinacnog zadatka je neuspesno!\nKomanda koja je pokrenuta:\n{0}'
								 .format(command))
			os.remove(a)

	util.clear_directory(config.TEMP_PATH)


def generate_empty_criteria_file(backend, filename, initial_project_path, autotest_path):
	"""
	Generiše se i snima default varijanta kriterijumskog fajla kako bi je korisnik mogao editovati

	U postavci zadatka se nalaze kandidati za relevantne fajlove u zadatku (fajlove u koje studenti unose svoje
	rešenje). Iz autotest varijante zadatka se učitavaju nazivi svih testova koji su prisutni u zadatku.

	backend - back-end koji se trenutno koristi
	filename - naziv pod kojim će se snimiti kriterijumski fajl
	initial_project_path - putanja na kojoj se nalazi postavka zadatka
	autotest_path - putanja na kojoj se nalazi autotest varijanta zadatka
	"""
	# Traženje svih fajlova sa relevantnim ekstenzijama u početnoj postavci zadatka:
	full_matches = []
	for pattern in backend.get_assignment_files_pattern():
		full_matches.extend(sorted(glob.glob(join(initial_project_path, pattern))))

	matches = []
	for m in full_matches:
		matches.append(os.path.basename(m))

	logging.debug('Pronadjeni su sledeci potencijalno relevantni fajlovi u postavci zadatka: {0}'.format(matches))

	tests = backend.get_test_names(autotest_path)

	tests_json = []
	for t in tests:
		tests_json.append({t : 10})

	runs = {'total' : 1, 'pass_limit' : 1.0 }
	data = {'backend' : backend.name(), 'files' : matches, 'tests' : tests_json, 'runs' : runs,
			'blockers' : [], 'total_points' : 20}

	with open(filename, 'wb') as f:
		json.dump(data, codecs.getwriter('utf-8')(f), ensure_ascii = False, indent = 4)


def wait_until_files_are_set(path):
	print bcolors.OKBLUE + 'Molim postavite fajlove u predvidjeni direktorijum' + bcolors.ENDC

	while os.listdir(path) == []:
		time.sleep(1)

	print bcolors.OKBLUE + 'Detektovano novih fajlova u direktorijumu: {0}.'.format(len(os.listdir(path))) \
		  + bcolors.ENDC
	raw_input('Pritisnite <ENTER> kada budete spremni za nastavak.')
