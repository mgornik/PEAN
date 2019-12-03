# -*- coding: utf-8 -*-

import logging
import json
import util

from os import path

class Criteria:
	"""
	Kriterijum za ocenjivanje zadataka

	Polja klase:
	backend_selection - koji back-end se koristi za ocenjivanje zadataka
	assignment_files - lista naziva fajlova u kojima se nalazi studentsko rešenje
	total_weight - ukupan težinski faktor za sve testove u konfiguraciji
	score_distribution - raspored težina i bodova po testovima
	blocking_tests - lista testova čiji pad uzrokuje ocenjivanje celog zadatka nulom
	total_points - ukupan broj poena koji nosi zadatak koji se pregleda
	runs_spec - specifikacija toga kako se pokreću testovi - koliko puta i kada se smatra da je test uspešan
	"""

	def read_criteria_file(self, config):
		if path.isfile(config.RATING_CRITERIA_FILENAME):
			logging.debug('Ucitavanje sadrzaja kriterijumskog fajla: "{0}"'.format(config.RATING_CRITERIA_FILENAME))
			with open(config.RATING_CRITERIA_FILENAME) as data_file:
				try:
					data = json.load(data_file)
				except ValueError:
					util.fatal_error('Fajl sa kriterijumom pregledanja nije u dobrom formatu!')

			try:
				self.backend_selection = data['backend']
				self.assignment_files = data['files']
				self.score_distribution = data['tests']
				self.blocking_tests = data['blockers']
				self.total_points = data['total_points']
			except KeyError as err:
				util.fatal_error('Podešavanje "{0}" nedostaje u kriterijumskom fajlu.'.format(err.message))

			# runs opcija nije obavezna. Ako se ne zada, koriste se podrazumevane vrednosti:
			if 'runs' in data:
				self.runs_spec = data['runs']
			else:
				self.runs_spec = {"total": 1, "pass_limit" : 1}

			# Formiranje ukupnog težinskog faktora - koji je zbir pojedinačnih težinskih faktora svih testova
			self.total_weight = 0
			for s in self.score_distribution:
				self.total_weight += s.values()[0]

			# Formiranje pojedinačnih procentualnih vrednosti testova - određuje se u odnosu na ta koliko procentualno 
			# iznosi težina datog testa u odnosu na ukupan težinski faktor
			for i, s in enumerate(self.score_distribution):
				self.score_distribution[i] = {s.keys()[0]: {
					"factor" : s.values()[0],
					"percent" : float(s.values()[0]) / self.total_weight * 100.00}}

			# Provera da li je lista blokirajućih testova validna:
			for b in self.blocking_tests:
				if self.score_distribution[b] is None:
					util.fatal_error('''Test pod nazivom "{0}" definisan je kao blokirajuc a pritom nije definisano bodovanje za njega (u fajlu sa kriterijumom ocenjivanja: "{1}")'''.format(b, config.RATING_CRITERIA_FILENAME))
		else:
			util.fatal_error('Kriterijumski fajl nije pronadjen pod nazivom: {0}'
							 .format(config.RATING_CRITERIA_FILENAME))

