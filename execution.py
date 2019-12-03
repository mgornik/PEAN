# -*- coding: utf-8 -*-

import logging
import util
import os
import os.path as path
import re
import final_report
import datetime
import sys
import fnmatch

from util import bcolors
from os.path import join
from Queue import Queue
from shutil import copyfile
from threading import Thread
from testing_results import TestResults
from assignment_status import *

def execute_build_command(backend, config, criteria, comp, stations, current_assignment_path, autobuild_path):
	"""
	Izvršenje komande koja obavlja kompajliranje zadatka

	backend - back-end koji se trenutno koristi
	config - globalna konfiguracija alata za pregled
	criteria - kriterijum pregleda zadatka (bodovanje, način izvršavanja itd.)
	comp - oznaka računara na kojem je urađen zadatak koji se pregleda
	stations - kolekcija računara i studenata koji su radili zadatak (ključ - oznaka računara, podatak - lista - broj
	           indeksa i ime/prezime studenta)
	current_assignment_path - putanja na kojoj se nalazi studentski zadatak koji se kompajlira
	autobuild_path - putanja na kojoj se nalazi autobuild varijanta tekućeg zadatka
	"""
	logging.info('Pokrenuto je kompajliranje tekuceg projekta u direktorijumu: {0}'.format(current_assignment_path))

	build_report_path = join(autobuild_path, backend.get_build_report_filename())

	code = internal_build_project(backend, config, criteria, current_assignment_path, autobuild_path)
	if code == 0:
		print bcolors.OKGREEN + 'Kompajliranje projekta je uspesno.' + bcolors.ENDC
	elif code == 1:
		print bcolors.FAIL + '''Kompajliranje projekta je generisalo upozorenja!
Mozete nastaviti sa izvrsenjem testova, ukoliko zelite da pregledate izvestaj o kompajliranju, on se nalazi u fajlu: "{0}"'''.format(backend.get_build_report_filename()) + bcolors.ENDC
	else:
		if vm_build_error(build_report_path):
			util.fatal_error('''Kompajliranje projekta je neuspesno. 
Razlog neuspeha je cinjenica da je sva virtuelna memorija potrosena.
Najbolje je da restartujete sistem pa potom nastavite pregled.''')
		else:
			print bcolors.FAIL \
				  + 'Kompajliranje projekta je neuspesno. Bice prikazan fajl ("{0}") sa izvestajem kompajliranja.'\
					  .format(backend.get_build_report_filename()) + bcolors.ENDC
			raw_input('Pritisnite <ENTER> za nastavak...')
			util.show_text_edit(config, build_report_path)
			final_report.update_final_report(config, criteria, stations, comp, datetime.datetime.now().isoformat(),
											 status=ASSIGNMENT_STATUS_FAILS_TO_COMPILE)
			sys.exit(0)


def execute_run_tests_command(backend, config, criteria, stations, run_path, comp):
	"""
	Izvršenje komande koja obavlja pokretanje svih testova za zadatak

	backend - back-end koji se trenutno koristi
	config - globalna konfiguracija alata za pregled
	criteria - kriterijum pregleda zadatka (bodovanje, način izvršavanja itd.)
	stations - kolekcija računara i studenata koji su radili zadatak (ključ - oznaka računara, podatak - lista - broj
	           indeksa i ime/prezime studenta)
	run_path - putanja na kojoj se nalazi studentski zadatak čiji se testovi izvršavaju
	comp - oznaka računara na kojem je urađen zadatak koji se pregleda
	"""	
	if not path.isdir(config.AUTOTEST_PATH):
		util.fatal_error('''Prilikom postavljanja zadatka nije postavljena autotest varijanta zadatka.\n'
Ako zelite da koristite automatsko testiranje, kreirajte direktorijum "{0}" i postavite autotest varijantu u njega.'''.format(config.AUTOTEST_PATH))

	if not path.isdir(run_path):
		util.fatal_error('Ne mogu se pokrenuti testovi jer projekat nije prethodno kompajliran.\n'
						 + 'Upotrebite komandu build za kompajliranje projekta.')

	util.make_sure_path_exists(config.REPORTS_PATH)
	current_reports_path = join(config.REPORTS_PATH, comp)
	util.make_sure_path_exists(current_reports_path)
	util.clear_directory(current_reports_path)

	logging.info('Pokrenuti su automatski testovi tekuceg projekta u direktorijumu: {0}'.format(run_path))

	proj = util.identify_project_file(backend, run_path)
	executable = backend.identify_project_executable(proj)

	all_results = []
	tests = []
	for s in criteria.score_distribution:
		tests.append(s.keys()[0])

	# Zakazivanje izvršenja testova od strane (potencijalno) više niti za izvršenje testova:

	print('Sledeci testovi ce biti izvrseni: {0}'.format(', '.join(tests)))
	print('Svaki test se izvrsava {0} put(a)'.format(criteria.runs_spec['total']))

	for t in tests:
		execution_results[t] = [None] * criteria.runs_spec['total']

	for i in range(backend.get_parallel_testing_threads_count()):
		t = Thread(target = execution_worker_thread, args = (backend, criteria, i, run_path, executable))
		t.daemon = True
		t.start()

	for t in tests:
		test_index = 0
		for run in range(1, criteria.runs_spec['total'] + 1):
			execution_queue.put([test_index, t, get_console_report_path(config, comp, t, test_index)])
			test_index += 1

	execution_queue.join()

	# Grupisanje dobijenih rezultata - konsolidacija rezultata po svakom pojedinačnom testu (po nazivu testa):

	for t in tests:
		results = execution_results[t]

		# Određivanje najdužeg vremena izvršenja ovog testa:
		max_duration = results[0].duration
		executions = []
		for r in results:
			if r.duration > max_duration:
				max_duration = r.duration
			executions.append(r.result == 'passed')

		passes = sum(1 for x in results if x.result == 'passed')

		entry = TestResults(name = t, 
							runs = criteria.runs_spec['total'],
			                passes = passes, 
			                failures = sum(1 for x in results if x.result != 'passed'),
			                test_fails = sum(1 for x in results if x.result == 'failed'), 
			                crashes = sum(1 for x in results if x.result == 'crashed'), 
			                time_outs = sum(1 for x in results if x.result == 'timed-out'),
			                total_duration = sum(x.duration for x in results),
			                max_duration = max_duration,
			                score = get_score(criteria, t)["percent"],
			                factor = get_score(criteria, t)["factor"],
			                success = (passes / float(criteria.runs_spec['total'])) >= criteria.runs_spec['pass_limit'],
			                executions = executions)

		all_results.append(entry)

	# Ispis rezimea pokretanja testova na konzolu:

	total = len(criteria.score_distribution)
	passed = 0
	score = 0
	blockers = False
	for t in all_results:
		print ''
		header_line = 'TEST: {0}, ukupno izvrsenja: {1}'.format(t.name, t.runs)
		print '*' * len(header_line)
		print bcolors.BOLD + header_line + bcolors.ENDC
		print '*' * len(header_line)

		if t.runs < criteria.runs_spec['total']:
			print bcolors.FAIL \
				  + 'Detektovano je dovoljno negativnih ishoda pa nije obavljeno svih {0} zahtevanih pokretanja'\
					  .format(criteria.runs_spec['total']) + bcolors.ENDC

		if t.passes > 0:
			print bcolors.OKGREEN + 'PROSAO: {0} put(a)'.format(t.passes) + bcolors.ENDC
		if t.failures > 0:
			print bcolors.FAIL + 'PAO: {0} put(a), od toga:'.format(t.failures) + bcolors.ENDC
			if t.test_fails > 0:
				print bcolors.FAIL + '    Formirao los rezultat:       {0} put(a)'.format(t.test_fails) + bcolors.ENDC
			if t.crashes > 0:
				print bcolors.FAIL + '    Nasilno prekinuo izvrsenje:  {0} put(a)'.format(t.crashes) + bcolors.ENDC
			if t.time_outs > 0:
				print bcolors.FAIL + '    Prekoracio dozvoljeno vreme: {0} put(a)'.format(t.time_outs) + bcolors.ENDC

		print 'Ukupno vreme izvrsenja: {0}, najduze pokretanje: {1}'.format(t.total_duration, t.max_duration)

		if t.success:
			print bcolors.OKGREEN + 'Test se smatra uspesnim, tezina: {0} (od ukupno {1}), procentualno: {2:.2f}%'\
				.format(t.factor, criteria.total_weight, t.score) + bcolors.ENDC
			passed += 1
			score += t.score
		else:
			print bcolors.FAIL + 'Test se smatra neuspesnim' + bcolors.ENDC
			if t in criteria.blocking_tests:
				blockers = True
				print bcolors.FAIL + 'Ovo je blokirajuci test!' + bcolors.ENDC

	print ''
	if passed == total:
		print bcolors.OKGREEN \
			  + '''Uspesno su izvrseni svi testovi (ukupno je: {0} testova).\nUkupno ostvareno procenata: {1:.2f}%'''.format(total, score) + bcolors.ENDC
	else:
		failed = total - passed
		print bcolors.FAIL + '''Palo je {0} testova, od ukupno {1}!
Procenat testova koji prolaze: {2:.2f}%, procentualni ucinak: {3:.2f}%'''.format(failed, total, float(passed) / total * 100.0, score) + bcolors.ENDC

	status = ASSIGNMENT_STATUS_OK
	if blockers:
		print bcolors.FAIL + bcolors.BOLD \
			  + 'Pao je makar jedan blokirajuci test! U izvestaju je naznaceno da u ovom radu postoje takvi testovi.' \
			  + bcolors.ENDC
		status = ASSIGNMENT_STATUS_BLOCKED

	final_report.update_final_report(config, criteria, stations, comp, datetime.datetime.now().isoformat(),
									 status=status, results=all_results)


def get_console_report_path(config, comp, test_name, unique_id):
	"""
	Pomoćna metoda koja vraća putanju do fajla sa konzolnim izlazom testa čiji je naziv dat

	Konzolni izlazi se čuvaju na putanji config.REPORTS_PATH, u poddirektorijumu čiji naziv odgovara računaru.

	config - globalna konfiguracija alata za pregled
	comp - oznaka računara na kojem je urađen zadatak koji se pregleda
	test_name - naziv testa čiji se konzolni izlaz ispituje
	unique_id - unikatni identifikator testa (jedan test dobija isti unikatni ID i taj se prosleđuje svim metodama koje
	            se bave izvršenjem testova)
	"""
	console_report_name = config.CONSOLE_REPORT_FILENAME.format(test_name, unique_id + 1)
	return os.path.join(config.REPORTS_PATH, comp, console_report_name)


def get_score(criteria, test_name):
	"""
	Vraća kriterijum ocenjivanja za zadati test

	criteria - kriterijum pregleda zadatka (bodovanje, način izvršavanja itd.)
	test_name - naziv testa čije se ocenjivanje preuzima
	"""
	for s in criteria.score_distribution:
		if s.keys()[0] == test_name:
			return s.values()[0]


# Red koji se koristi za prosleđivanje testova nitima koje se koriste za pokretanje niti:
execution_queue = Queue()
# Rezultati izvršenja testova (niti popunjavaju ovu kolekciju):
execution_results = {}


def do_execute(backend, criteria, ind, execute_dir, executable_file_path, test_index, test_name, report_path):
	"""
	Funkcija koja obavlja zadatak radne niti za pokretanja testa

	backend - back-end koji se trenutno koristi
	criteria - kriterijum pregleda zadatka (bodovanje, način izvršavanja itd.)
	ind - indeks pokretanja testa (1..N) - za svaki novi test kreće od jedinice
	execute_dir - direktorijum u kojem se inicira izvršenje
	executable_file_path - relativna putanja do izvršnog fajla (uključujući i njegov naziv) - relativna u odnosu na
	                       execute_dir
	test_index - unikatni identifikator pokretanja testa
	test_name - naziv testa koji se izvršava
	report_path - putanja do fajla sa konzolnim izlazom testa (uključujući i njegov naziv)

	Vraća interni format (objekat klase SingleRunResult) o uspešnosti pokretanja		
	"""
	backend.execute_test(test_name, execute_dir, executable_file_path, test_index, report_path)

	try:
		r = backend.parse_testing_artefacts(test_name, execute_dir, criteria.blocking_tests, test_index)
		return r

	except RuntimeError as err:
		util.fatal_error(err.message)


def execution_worker_thread(backend, criteria, ind, execute_dir, executable_file_path):
	"""
	Funkcija koju izvršavaju radne niti koje obrađuju pokretanje testova

	backend - back-end koji se trenutno koristi
	criteria - kriterijum pregleda zadatka (bodovanje, način izvršavanja itd.)
	ind - indeks pokretanja testa (1..N) - za svaki novi test kreće od jedinice
	execute_dir - direktorijum u kojem se inicira izvršenje
	executable_file_path - relativna putanja do izvršnog fajla (uključujući i njegov naziv) - relativna u odnosu na
	                       execute_dir

	Red testova koje treba pokrenuti formira se u globalnom redu execution_queue.
	Rezultat pokretanja testova se agregira u globalnom dictionary-ju execution_results. 
	Ključ ovog rečnika je naziv testa, podatak je lista koja sadrži rezime svakog pojedinačnog pokretanja.
	"""
	logging.debug('Radna nit za pokretanje testova pod indeksom {0} je pokrenuta'.format(ind))
	logging.debug('Parametri niti: run_path: "{0}", executable: "{1}"'.format(execute_dir, executable_file_path))
	while True:
		item = execution_queue.get()
		test_index = item[0]
		test_name = item[1]
		report_path = item[2]

		logging.debug('Nit {0} preuzela je test pod indeksom: {1}, naziv testa: {2}'.format(ind, test_index, test_name))
		execution_results[test_name][test_index] = do_execute(backend, criteria, ind, execute_dir, executable_file_path,
															  test_index, test_name, report_path)
		execution_queue.task_done()
		logging.debug('Nit {0} zavrsila je pokretanje testa'.format(ind))


def filename_matches_assignment_pattern(backend, file):
	for m in backend.get_assignment_files_pattern():
		if fnmatch.fnmatch(file, m):
			return True

	return False


def internal_build_project(backend, config, criteria, current_assignment_path, autobuild_path):
	"""
	Interna pomoćna metoda koja vrši kompajliranje projekta (studentskog zadatka)

	backend - back-end koji se trenutno koristi
	config - globalna konfiguracija alata za pregled
	criteria - kriterijum pregleda zadatka (bodovanje, način izvršavanja itd.)
	current_assignment_path - putanja do zadatka koji se kompajlira
	autobuild_path - putanja na kojoj se nalazi autobuild varijanta tekućeg zadatka

	Vraća indikaciju da li je kompajliranje uspešno obavljeno
	0 - kompajliranje je uspešno
	1 - produkovan je izvršni fajl ali je kompajliranje vratilo upozorenja
	2 - kompajliranje je neuspešno
	"""
	logging.info('Pokrenuto je kompajliranje projekta u direktorijumu: {0}'.format(current_assignment_path))

	# Brisanje trenutnog sadrzaja autobuild direktorijuma:
	print('Brisanje sadrzaja direktorijuma "{0}"'.format(autobuild_path))
	util.make_sure_path_exists(autobuild_path)
	util.clear_directory(autobuild_path)

	# Kopiranje svih fajlova iz osnovnog direktorijuma u autobuild poddirektorijum:
	print('Kopiranje izvornih fajlova iz "{0}" u "{1}"'.format(current_assignment_path, autobuild_path))
	onlyfiles = [f for f in os.listdir(current_assignment_path) if path.isfile(join(current_assignment_path, f))]	
	autotestfiles = [f for f in os.listdir(config.AUTOTEST_PATH) if path.isfile(join(config.AUTOTEST_PATH, f))]

	for f in onlyfiles:
		if (f in criteria.assignment_files) or (f not in autotestfiles and filename_matches_assignment_pattern(backend, f)):
			copyfile(join(current_assignment_path, f), join(autobuild_path, f))

	# Obrada događaja koji se inicira pre nego što se obavi kompajliranje zadatka:
	try:
		backend.before_build(autobuild_path)
	except RuntimeError as err:
		util.fatal_error(err.message)

	# Kopiranje dodatnih fajlova iz autotest direktorijuma u autobuild poddirektorijum:
	print('Kopiranje autotest fajlova iz "{0}" u "{1}"'.format(config.AUTOTEST_PATH, autobuild_path))

	if len(autotestfiles) == 0:
		util.fatal_error(
			'Projekat se ne moze kompajlirati jer autotest varijanta zadatka nije postavljena u direktorijum: "{0}"!'
				.format(config.AUTOTEST_PATH))

	for f in autotestfiles:
		# Proverava se da li je fajl naveden u listi fajlova u kojima studenti unose resenje zadatka.
		# Ako je tako, onda taj fajl ne bi smeo da bude postavljen u autotest folder.
		if f in criteria.assignment_files:
			util.fatal_error('''Fajl "{0}" je postavljen u "{1}" direktorijum a ocekuje se da studenti unose svoje resenje u taj fajl.
Fajlovi iz "{1}" direktorijuma kopiraju se preko studentskog resenja, tako da bi kopiranjem ovog fajla unistili kljucni deo resenja.
Molim da procitate deo uputstva za koriscenje alata za pregled koji se odnosi na postavljanje fajlova u ovaj direktorijum.'''.format(f, config.AUTOTEST_PATH))

		copyfile(join(config.AUTOTEST_PATH, f), join(autobuild_path, f))

	# Potom, sledi kompajliranje projekta:
	ret = backend.build_project(util.identify_project_file(backend, autobuild_path))

	# Poslednja linija izvešaja o kompajliranju treba da sadrži informaciju o potencijalnim upozorenjima i greškama tokom kompajliranja:
	
	f = open(join(autobuild_path, backend.get_build_report_filename()), 'r') 
	lines = f.readlines()
	last_line = lines[len(lines)-1]
	regex = re.compile('(?P<errors>\d+)\serror\(s\),\s(?P<warnings>\d+)\swarning\(s\)', re.IGNORECASE)
	m = regex.match(last_line)

	if m:
		errors = int(m.group('errors'))
		warnings = int(m.group('warnings'))

		if (errors == 0 and warnings == 0):
			return 0

		if (errors == 0):
			return 1

		return 2
	else:
		util.fatal_error('''Interna greska: izvestaj o kompajliranju ne sadrzi poslednju liniju sa brojem gresaka i upozorenja.
Nije moguce utvrditi ishod kompajliranja. Potrebno je kontaktirati autora alata.''')


def vm_build_error(build_report_path):
	"""
	Ispituje da li je greška u kompajliranju posledica problema sa Code::Blocks okruženjem

	build_report_path - putanja do izveštaja o kompajliranju projekta
	"""
	f = open(build_report_path, 'r') 
	text = f.read()
	regex = re.compile('^virtual memory exhausted', re.MULTILINE | re.IGNORECASE)
	m = regex.search(text)
	return not m is None