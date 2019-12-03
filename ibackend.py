# -*- coding: utf-8 -*-

import logging
import glob
import os
import fnmatch
import re

from os import path
from abc import ABCMeta, abstractmethod
from os.path import join

# Interfejs ka back-end implementaciji (ona pruza podršku konkretnom programskom jeziku i razvojnom okruženju)
class IBackend:
	__metaclass__ = ABCMeta

	@abstractmethod
	def name(self):
		"""
		Naziv back-end-a
		"""
		raise NotImplementedError


	@abstractmethod
	def version(self):
		"""
		Verzija back-end-a
		"""
		raise NotImplementedError


	@abstractmethod
	def description(self):
		"""
		Opis back-end-a (za koji programski jezik i okruženje se koristi)
		"""
		raise NotImplementedError


	@abstractmethod
	def get_project_pattern(self):
		"""
		Vraća obrazac za naziv fajla koji sadrži projekat

		Primer validne vrednosti: *.cbp

		Koristi se prilikom ispisa kako bi se prikazao obrazac koji se koristi kako bi se locirao projektni fajl
		zadatka.
		"""
		raise NotImplementedError


	@abstractmethod
	def get_assignment_files_pattern(self):
		"""
		Vraća listu obrazaca za nazive fajlova koje sadrži studentski zadatak (samo source fajlova koji su relevantni
		za pregled)

		Primer validne vrednosti: ["*.h", "*.cpp"]
		"""
		raise NotImplementedError


	@abstractmethod
	def get_ignore_files_pattern(self):
		"""
		Vraća listu obrazaca za nazive fajlova koji se ignorišu prilikom izvršenja diff komandi

		Primer validne vrednosti: ["*.depend", "*.layout", "*.cbp"]
		"""
		raise NotImplementedError


	def identify_project_file(self, project_dir_path): 
		"""
		Pronalazi projektni fajl na zadatoj putanji (samo na njoj, pretraga nije rekurzivna)

		Pretraga koristi obrazac za naziv fajla koji sadrži projekat koji vraća metoda get_project_pattern()
		
		project_dir_path - putanja koja se pretražuje

		Vraća listu sa svim pronađenim kandidatima za projektni fajl
		"""
		return glob.glob(join(project_dir_path, self.get_project_pattern()))


	def find_project_recursive(self, project_dir_path):
		"""
		Pronalazi projektni fajl unutar zadate putanje (u bilo kom poddirektorijumu zadate putanje, pošto rekurzivno
		traži)

		Pretraga koristi obrazac za naziv fajla koji sadrži projekat koji vraća metoda get_project_pattern()

		project_dir_path - putanja koja se rekurzivno pretražuje

		Vraća listu sa putanjama svih poddirektorijuma koji sadrže projektni fajl (može ih biti nula, jedan ili više od
		jednog)
		"""
		matches = []
		for root, dirnames, filenames in os.walk(project_dir_path):
			for filename in fnmatch.filter(filenames, self.get_project_pattern()):
				matches.append(root)

		return matches


	@abstractmethod
	def identify_project_executable(self, project_file_path):
		"""
		Na osnovu zadatog projektnog fajla određuje kako se zove izvršni fajl koji se dobija kompajliranjem projekta

		project_file_path - putanja do projektnog fajla (uključujući i njegov naziv)

		Vraća naziv izvršnog fajla (naziv može biti fiksiran ili može biti pročitan iz projektnog fajla)
		"""
		raise NotImplementedError


	@abstractmethod
	def build_project(self, project_file_path):
		"""
		Kompajlira projekat

		project_file_path - putanja do projektnog fajla (uključujući i njegov naziv)

		Vraća statusni kod dobijen prilikom izvršenja kompajlera (0 indikuje da je kompajliranje uspešno)
		"""
		raise NotImplementedError


	@abstractmethod
	def get_build_report_filename(self):
		"""
		Vraća naziv fajla koji sadrži izveštaj o kompajliranju projekta
		"""


	@abstractmethod
	def get_parallel_testing_threads_count(self):
		"""
		Vraća broj niti koje mogu da izvršavaju testove u paraleli (treba da vrati 1 ako paralelno izvršenje nije
		potrebno ili dozvoljeno)
		"""


	@abstractmethod
	def execute_test(self, test_name, execute_dir, executable_file_path, unique_id, report_path):
		"""
		Izvršava kompajlirani projekat sa zadatim nazivom, na zadatoj putanji (izvršava se jedan izabrani test)

		Test koji izvrši ova metoda treba da svoj rezultat upiše u eksterne artefakte (na primer fajlove) kako bi metoda
		koja interpretira rezultate imala dostupne rezultate izvršenja.
		Pritom, ako su potrebna paralelna izvršenja više testova, neophodno je da su artefakti takvi da ne pregaze jedni
		druge tokom izvršenja. Da bi se to postiglo, može se koristiti zadati parametar unique_id.

		test_name - naziv testa koji se izvršava
		execute_dir - direktorijum u kojem se inicira izvršenje
		executable_file_path - relativna putanja do izvršnog fajla (uključujući i njegov naziv) - relativna u odnosu na
		                       execute_dir
		unique_id - unikatni identifikator testa (može se koristiti kako bi se generisali unikatni nazivi fajlova i sl.)
		report_path - putanja do fajla sa konzolnim izlazom testa (uključujući i njegov naziv)
		"""
		raise NotImplementedError


	@abstractmethod
	def parse_testing_artefacts(self, test_name, dir_path, blocking_tests, unique_id):
		"""
		Parsira artefakte koji je generisalo izvršavanje projekta i popunjava interni format o rezultatu izvršenja

		Metoda execute_project() eksterno čuva rezultate izvršenja projekta (artefakte). Ova metoda treba da parsira te
		artefakte kako bi formirala rezultate izvršenja.

		test_name - naziv testa čiji se rezultati parsiraju
		dir_path - putanja na kojoj se nalaze artefakti dobijeni pokretanjem testa
		blocking_tests - lista koja sadrži nazive blokirajućih testova
		unique_id - unikatni identifikator testa (jedan test dobija isti unikatni ID i taj se prosleđuje ovoj metodi i
		            metodi execute_test())

		Vraća interni format (objekat klase SingleRunResult) o uspešnosti pokretanja		
		"""
		raise NotImplementedError


	@abstractmethod
	def get_test_names(self, autotest_path):
		"""
		Iz autotest varijante zadatka čita nazive svih testova koji postoje u zadatku.

		Koristi se samo kod formiranja početnog kriterijumskog fajla (init komanda nudi početnu verziju ovog fajla).

		autotest_path - putanja na kojoj se nalazi autotest varijanta zadatka

		Vraća listu stringova koji predstavljaju nazive testova.
		"""
		raise NotImplementedError


	def after_assignment_loaded(self, current_assignment_path, project_file_name):
		"""
		Događaj koji se poziva nakon što je studentski zadatak učitan

		Konkretan back-end može iskoristiti ovu metodu kako bi obavio dodatno procesiranje nakon učitavanja zadatka.

		current_assignment_path - putanja do učitanog zadatka
		project_file_name - naziv projektnog fajla
		"""
		pass


	def before_build(self, dir_path):
		"""
		Događaj koji se poziva pre nego što se pokrene kompajliranje studentskog zadatka

		dir_path - putanja do učitanog zadatka
		"""
		pass


	def apply_replacements(self, replacements, dir_path):
		"""
		Primenjuje tekstualne zamene menjajući sadržaj fajlova na datoj putanji

		replacements - konfiguracija zamena
		dir_path - direktorijum u kojem se pretražuju fajlovi i sadržaj tih fajlova se menja
		"""
		for repl in replacements:
			for file_pattern, r in repl.items():
				files = [f for f in os.listdir(dir_path) if path.isfile(join(dir_path, f))]
				for filename in fnmatch.filter(files, file_pattern):
					logging.debug('Fajl "{0}" se poklapa sa patternom: "{1}", primenjuju se zamene u tom fajlu'
								  .format(filename, file_pattern))
					file_path = join(dir_path, filename)
					with open (file_path, "r") as rfile:
						text = rfile.read()
					for find, replace in r.items():
						ret = re.subn(find, replace, text, flags=re.MULTILINE | re.IGNORECASE)
						if ret[1] == 0:
							raise RuntimeError('''Interna greska: nije uspela zamena teksta u fajlu "{0}"!
Gresku prijaviti autoru programa.'''.format(filename))
						text = ret[0]
					with open (file_path, "w") as wfile:
						wfile.write(text)
