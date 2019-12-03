# -*- coding: utf-8 -*-

import util

from os import path
# LXML se koristi za čitanje i upis finalnog izveštaja u XML formatu.
# U odnosu na sistemsku XML biblioteku, LXML omogućava bolju podršku za indentaciju, UTF-8 karakter set i XSLT dokument. 
from lxml import etree
from lxml import objectify

from assignment_status import *

def update_final_report(config, criteria, stations, station, time, status = None, comment = None, results = None,
						score = None, correction = None):
	"""
	Ažurira finalni izveštaj sa pojedinačnim elementom ocene zadatka

	Mehanizam rada je takav da će menjati samo jedan <assignment> nod u XML fajlu i to onaj koji se tiče zadatka kojem
	se prijavljuju izmene u rezultatu. Ostatak sadržaja neće biti učitavan i menjan.

	config - globalna konfiguracija alata za pregled
	criteria - kriterijum pregleda zadatka (bodovanje, način izvršavanja itd.)
	stations - kolekcija računara i studenata koji su radili zadatak (ključ - oznaka računara, podatak - lista - broj
	           indeksa i ime/prezime studenta)
	station - oznaka računara na kojem je zadatak urađen
	time - timestamp poslednje izmene na rezultatima
	status - status celog zadatka
	comment - komentar pregledača na zadatak
	results - lista tuple objekata TestResults - rezultat izvršenja testova
	score - procentualni učinak studenta na zadatku
	correction - korekcija koju je pregledač uveo
	"""
	print 'Azuriranje XML fajla sa izvestajem sa ispita: "{0}"'.format(config.FINAL_REPORT_FILENAME)

	try:
		criteria.total_points # Provera da li je definisana varijabla
	except NameError:
		criteria.total_points = 100

	total_points_f = float(criteria.total_points)

	if not (results is None):
		total = 0.0
		for r in results:
			if r.success:
				total += r.score

	# Ako fajl ne postoji, kreiraj korenski element:
	if not(path.isfile(config.FINAL_REPORT_FILENAME)):
		root = objectify.Element('assignments')
	else:
		with open(config.FINAL_REPORT_FILENAME) as f:
			xml = f.read()
 
		root = objectify.fromstring(xml)

	# Probaj pronaci <assignment> tag koji se odnosi na zadatu stanicu:
	assign = None
	for a in root.getchildren():
		if a.get('station') == station:
			assign = a

	# Ako prethodno ne postoji takav <assignment>, kreiraj novi:
	if assign == None:
		assign = objectify.SubElement(root, 'assignment')
		# Podesi nove podatke:
		assign.set('station', station)
		assign['id'] = stations[station][0]
		assign['name'] = stations[station][1]

	# Podesi nove podatke:
	assign.time = time

	if not (results is None):
		assign['test-score'] = '{:.2f}'.format(total)

	if not (comment is None):
		assign['comment'] = comment

	if not (score is None):
		assign['direct-score'] = '{:.2f}'.format(score)
		assign['final-pct'] = '{:.2f}'.format(score)

	if not (correction is None):
		# Ako je zadata korekcija 0 - onda se korekcija ukida:
		if correction == 0:
			sub = assign.find('correction')
			if (sub is not None):
				assign.remove(sub)

		else:
			assign['correction'] = '{:+.2f}'.format(correction)

		final_number = 0
		reason = u'nema uspešnih testova'
		if assign.find('test-score') is not None:
			final_number = float(assign['test-score'])
			reason = u'{:+.2f}% na uspešne testove'.format(final_number)
		if correction != 0:
			final_number = final_number + correction
			reason = reason + u' i {:+.2f}% korekcija'.format(correction)
		
		final = '{:.2f}'.format(final_number)
		points = int(round(final_number * (total_points_f / 100.0), 0))

		assign['final-pct'] = final
		assign['final-points'] = points
		assign['reason'] = reason

	if not (results is None):
		# Ako je bilo direktno zadatog rezultata, nakon što su izvršeni automatski testovi, taj skor se briše:
		sub = assign.find('direct-score')
		if (sub is not None):
			assign.remove(sub)

		while True:
			sub = assign.find('tests')
			if (sub is None):
				break;
			assign.remove(sub)
		
		tests_root = objectify.SubElement(assign, 'tests')
		for r in results:
			test = objectify.SubElement(tests_root, 'test')
			test.attrib['name'] = r.name
			test['runs'] = r.runs
			test['passes'] = r.passes
			test['failures'] = r.failures
			test['test-fails'] = r.test_fails
			test['crashes'] = r.crashes
			test['time-outs'] = r.time_outs
			test['total-duration'] = '{:.2f}'.format(r.total_duration)
			test['max-duration'] = '{:.2f}'.format(r.max_duration)
			test['success'] = r.success
			test['score'] = '{:.2f}'.format(r.score)
			test['factor'] = r.factor

			executions = objectify.SubElement(test, 'executions')
			for e in r.executions:
				elem = objectify.SubElement(executions, 'passed')
				elem._setText(str(e).lower())

	# Logika za odredjivanje broja poena, u odnosu na status rada i ostale parametre:
	if not (status is None):
		assign['status'] = status

		if status == ASSIGNMENT_STATUS_BLOCKED:
			final = '0'
			points = 0
			reason = u'makar jedan od blokirajućih testova ne prolazi'

		elif status == ASSIGNMENT_STATUS_FAILS_TO_COMPILE:
			final = '0'
			points = 0
			reason = u'projekat se ne kompajlira uspešno'

		elif status == ASSIGNMENT_STATUS_DIRECTLY_RATED:
			final = assign['direct-score']
			final_number = float(assign['direct-score'])
			points = int(round(final_number * (total_points_f / 100.0), 0))

			reason = u'direktno zadata ocena'

		elif status == ASSIGNMENT_STATUS_OK:
			final_number = float(assign['test-score'])
			reason = u'{0}% na uspešne testove'.format(final_number)
			sub = assign.find('correction')
			if (sub is not None):
				corr = float(assign['correction'])
				final_number = final_number + corr
				reason = reason + u' i {:+.2f}% korekcija'.format(corr)
			final = '{:.2f}'.format(final_number)
			points = int(round(final_number * (total_points_f / 100.0), 0))

		elif status == ASSIGNMENT_STATUS_SKIPPED:
			final_number = 0
			points = 0
			final = '{:.2f}'.format(final_number)
			reason = u'rad je preskočen'

		else:
			util.fatal_error('''Interna greska: status "{0}" nema definisana pravila za bodovanje!
Kontaktirati autora programa.'''.format(status))

		assign['final-pct'] = final
		assign['final-points'] = points
		assign['reason'] = reason

	# Upiši izmenjen fajl:
	f = open(config.FINAL_REPORT_FILENAME, 'w')
	objectify.deannotate(root)	# Skidanje objectify anotacija
	# Dodaje se XML zaglavlje u kojem se navodi UTF-8 kao upotrebljeno enkodiranje i referencira se XSLT dokument:
	f.write('<?xml version="1.0" encoding="UTF-8"?>\n<?xml-stylesheet type="text/xsl" href="{0}"?>\n'
			.format(config.FINAL_REPORT_XSLT_FILENAME))
	f.write(etree.tostring(root, xml_declaration=False, encoding='utf-8', pretty_print=True))
	f.close()