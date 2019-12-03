# -*- coding: utf-8 -*-

import os
import errno
import shutil
import fnmatch
import sys

from subprocess import call

class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'


def fatal_error(text):
	"""
	Prikaz greške i zaustavljanje rada programa uz povratni kod koji indikuje grešku

	text - tekst greške koji će biti prikazan
	"""
	print bcolors.FAIL + bcolors.BOLD + text + bcolors.ENDC
	sys.exit(1)


def clear_directory(path):
	"""
	Rekurzivno briše sadržaj date putanje (sve fajlove koji se nalaze na toj putanji kao i sve poddirektorijume i sav
	njihov sadržaj)

	path - putanja koja se rekurzivno briše
	"""
	for root, dirs, files in os.walk(path):
		for f in files:
			os.unlink(os.path.join(root, f))
		for d in dirs:
			shutil.rmtree(os.path.join(root, d))


def make_sure_path_exists(path):
	"""
	Ako putanja ne postoji, kreira se

	path - putanja koja se kreira, ukoliko već ne postoji
	"""
	try:
		os.makedirs(path)
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise


def get_option_answer(minimal, maximal):
	"""
	Preuzima odgovor korisnika sa tastature (očekuje se ceo broj u datom opsegu)

	minimal - najniža dozvoljena vrednost
	maximal - najviša dozvoljena vrednost

	Vraća vrednost koju je uneo korisnik (ponavljaće se unos dok god korisnik ne unese validan podatak)
	"""
	while True:
		answer_str = raw_input('Izaberite opciju ({0}-{1}): '.format(minimal, maximal))
		try:
			value = int(answer_str)
			if value >= minimal and value <= maximal:
				return value
			else:
				raise ValueError
		except ValueError:
			print 'Molim Vas da izaberete jednu od opcija ili pritisnete Ctrl+C za prekid!'


def get_yesno_answer(text):
	"""
	Preuzima odgovor korisnika sa tastature (očekuje se potvrda - da/ne odgovor)

	Vraća vrednost koju je uneo korisnik - u boolean obliku (ponavljaće se unos dok god korisnik ne unese validan
	podatak)
	"""
	while True:
		answer_str = raw_input(text + ' (D/N) ')
		if answer_str.lower() == 'd':
			return True
		elif answer_str.lower() == 'n':
			return False
		else:
			print 'Molim vas da izaberete jednu od dve ponudjene opcije (D/N) ili pritisnite Ctrl+C za prekid!'


def filename_matches(file_name, patterns):
	"""
	Ispituje da li zadati naziv fajla odgovara bilo kojem obrascu datom u listi patterns

	file_name - naziv fajla koji se ispituje
	patterns - lista stringova - obrasci koji se koriste

	Vraća indikaciju da li naziv fajla odgovara makar jednom zadatom obrascu
	"""
	for p in patterns:
		if fnmatch.fnmatch(file_name, p):
			return True

	return False


def cmp_files_ignore_newlines(path_1, path_2):
	"""
	Poredi sadržaj dva fajla, dozvoljavajući da se razlikuju markeri za new-line u fajlovima

	Indikuje da li su fajlovi identičnog sadržaja (ignorišu se newline markeri)
	"""
	l1 = l2 = ' '
	with open(path_1, 'r') as f1, open(path_2, 'r') as f2:
		while l1 != '' and l2 != '':
			l1 = f1.readline()
			l2 = f2.readline()
			if l1.rstrip('\r\n') != l2.rstrip('\r\n'):
				return False
	return True


def identify_project_file(backend, project_path):
	"""
	Pronalazi projektni fajl na zadatoj putanji (samo na njoj, pretraga nije rekurzivna) i osigurava da zaista postoji
	samo jedan takav fajl

	Ukoliko ima više kandidata za projektni fajl ili nema ni jednog, prijavljuje se greška i prekida se rad programa

	Vraća punu putanju (uključujući naziv fajla) do projektnog fajla

	backend - back-end koji se trenutno koristi
	project_path - putanja do projekta
	"""
	matches = backend.identify_project_file(project_path)

	if len(matches) == 0:
		fatal_error('Nije pronadjen projektni fajl u direktorijumu: {0} (pattern koji se trazi: "{1}")'
					.format(project_path, backend.get_project_pattern()))
	if len(matches) > 1:
		fatal_error('Pronadjeno je vise od jednog fajla koji je kandidat za projektni fajl. Kandidati: {0}'
					.format(matches))

	return matches[0]


def show_text_edit(config, f):
	"""
	Otvara izabrani tekstualni editor kako bi se prikazao/editovao zadati fajl

	config - globalna konfiguracija alata za pregled	
	f - fajl koji se otvara	
	"""
	command = config.TEXT_EDIT_CMD.format(f)
	ret = call(command, shell=True)
	if ret != 0:
		fatal_error('Pokretanje tekstualnog editora nije uspelo!\nKomanda koja je pokrenuta:\n{0}'.format(command))
