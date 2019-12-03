# -*- coding: utf-8 -*-

import util

from os import path
from subprocess import call
from assignment_status import *
from lxml import etree
from lxml import objectify


def execute_export_command(config, criteria, stations):
	"""
	Izvršavanje komande koja vrši izvoz rezultata u format koji se može lako uvesti u Evidenciju

	config - globalna konfiguracija alata za pregled
	criteria - kriterijum pregleda zadatka (bodovanje, način izvršavanja itd.)
	stations - kolekcija računara i studenata koji su radili zadatak (ključ - oznaka računara, podatak - lista - broj
	           indeksa i ime/prezime studenta)
	"""
	error_message = 'Interna greška: format XML fajla nije validan!\nFajl čije parsiranje nije uspelo: {0}'\
		.format(config.FINAL_REPORT_FILENAME)

	if not(path.isfile(config.FINAL_REPORT_FILENAME)):
		util.fatal_error('Ne može se izvršiti izvoz podataka pošto fajl sa izveštajem još uvek ne postoji!')
	else:
		with open(config.FINAL_REPORT_FILENAME) as f:
			xml = f.read()
 
		root = objectify.fromstring(xml)

	# Provera dve uslova:
	# 1) Da li su svi radovi ocenjeni?
	# 2) Da li postoje preskočeni radovi u izveštaju?
	# Ako je bilo koji od ovih uslova tačan, izvoz rezultata nije moguć:

	done_stations = {}
	for child in root.getchildren():
		if child.tag != 'assignment':
			util.fatal_error(error_message)
		if child['status'] == ASSIGNMENT_STATUS_SKIPPED:
			util.fatal_error('Ne može se izvršiti izvoz rezultata jer postoje preskočeni radovi!\n'
							 + 'Molim da ocenite ove radove pa pokušate izvoz ponovo.')
		done_stations[child.attrib['station']] = 1

	if set(stations) != set(done_stations):
		util.fatal_error('Ne može se izvršiti izvoz rezultata jer nisu svi radovi ocenjeni!\n'
						 + 'Molim da ocenite ove radove pa pokušate izvoz ponovo.')

	try:
		criteria.total_points # Provera da li je definisana varijabla
	except NameError:
		criteria.total_points = 100

	total_points_f = float(criteria.total_points)

	with open (config.EXPORTED_REPORT_FILENAME, 'w') as wfile:
		
		# Upis zaglavlja u CSV fajl:
		wfile.write('indeks,ime,prezime,poeni,ukupno_poena,ip,datum\n')

		for child in root.getchildren():
			if child.tag != 'assignment':
				util.fatal_error(error_message)

			indeks = child['id']
			naziv = child['name'].text
			razmak = naziv.find(' ')

			# Odredjivanje imena i prezimena:
			if razmak == -1:
				ime = naziv
				prezime = ''
			else:
				ime = naziv[:razmak]
				prezime = naziv[razmak+1:]

			final_score = float(child['final-pct'])
			poeni = int(round(final_score * (total_points_f / 100.0), 0))

			wfile.write('"{0}","{1}","{2}",{3},{4},,\n'.format(indeks, ime, prezime, poeni, criteria.total_points))

	command = config.COMPRESS_REPORT_COMMAND
	ret = call(command, shell=True)
	if ret != 0:
		util.fatal_error('''Pokretanje alata za komprimovanje CSV izveštaja u ZIP arhivu nije uspelo!
Komanda koja je pokrenuta:\n{0}'''.format(command))

	print 'Završen je izvoz podataka. Arhiva {0} sadrži rezultate pregleda.'.format(config.EXPORTED_ARCHIVE_FILENAME)