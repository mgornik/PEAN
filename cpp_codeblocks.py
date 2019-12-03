# -*- coding: utf-8 -*-

import logging
import os
import os.path as path
import json
import re
import util
import xml.etree.ElementTree as ElementTree	# Za čitanje gtest XML izveštaja sa rezultatima testiranja

from ibackend import IBackend
from os.path import join
from os.path import basename
from subprocess import call
from testing_results import SingleRunResult

# Back-end implementacija koja se zasniva na C++ kao programskom jeziku i Code::Blocks kao razvojnom okruženju:
class CPP_CodeBlocks(IBackend):
	def name(self): return "os_cpp_cb"

	def version(self): return "1.0"

	def description(self): return "Operativni Sistemi (g++0x/Code::Blocks)"    


	def __init__(self, execution_timeout, autobuild_path, alt_autobuild_path):
		"""
		Učitavanje konfiguracije back-end-a iz konfiguracionog fajla
		"""

		self.CONFIG_FILENAME = "cpp_codeblocks.config.json"
		self.execution_timeout = execution_timeout

		dir = os.path.dirname(__file__)
		with open(os.path.join(dir, self.CONFIG_FILENAME)) as data_file:    
			data = json.load(data_file)

		self.parallel_testing_threads_count = data['ParallelTestingThreadsCount']
		self.project_pattern = data['ProjectPattern']
		self.assignment_files_pattern = data['AssignmentFilesPattern']
		self.ignore_files_pattern = data['IgnoreFilesPattern']

		self.enforce_my_compiler = data['EnforceMyCompiler']
		self.my_compiler = data['MyCompiler']

		self.launch_codeblocks_on_assignment_open = data['LaunchCodeBlocksOnAssignmentOpen']

		self.build_report_filename = data['BuildReportFilename']
		self.gtest_testing_report_filename = data['GtestTestingReportFilename']
		self.gtest_testing_report_status_filename = data['GtestTestingReportStatusFilename']

		self.open_project_cmd = data['OpenProjectCommand']
		self.build_cmd = data['BuildCommand']
		self.execute_project_cmd = data['ExecuteProjectCommand']

		# Zamene koje se obavljaju prilikom izvršenja build komande:
		self.assignment_build_replacements = [{'niti.h':
												   {'(^\s*#ifndef\s*(?P<header>\w+)\s*#define\s*(?P=header))':
														r'\1\n#include "test_thread.h"\n#define thread test_thread'}},
		                                      {'vise_niti.h':
												   {'(^\s*#ifndef\s*(?P<header>\w+)\s*#define\s*(?P=header))':
														r'\1\n#include "test_thread.h"\n#define thread test_thread'}}]
		# Preusmeravanje sa STL thread klase na testabilnu klasu test_thread

		self.test_names_regex = re.compile('^\s*TEST\s*\(([^)]+)\)', re.MULTILINE)
                                    

	def get_project_pattern(self):
		return self.project_pattern


	def get_assignment_files_pattern(self):
		return self.assignment_files_pattern


	def get_ignore_files_pattern(self):
		return self.ignore_files_pattern


	def identify_project_executable(self, project_file_path):
		# Unutar projektnog fajla pronalazi podešavanje koje navodi kako se zove izvršni fajl projekta.
		# Putanja i naziv izvršnog fajla čitaju se iz atributa output koji pripada nodu Output (koji se nalazi u
		# Project/Build/Target).
		root = ElementTree.parse(project_file_path).getroot()
		return root.find('Project/Build/Target/Option').attrib['output']


	def build_project(self, project_file_path):
		command = format(self.build_cmd.format(basename(project_file_path), self.build_report_filename))
		logging.debug('Komanda za kompajliranje projekta: {0}'.format(command))
		return call(command, shell=True, cwd=path.dirname(project_file_path))


	def get_build_report_filename(self):
		return self.build_report_filename


	def get_testing_report_filename(self, test_name, unique_id):
		"""
		Pomoćna metoda koja vraća naziv fajla sa izveštajem o pokretanju testa čiji je naziv dat

		Izveštaj o pokretanju je XML fajl koji generiše gtest biblioteka prilikom pokretanja testa

		test_name - naziv testa čiji se izveštaj o pokretanju pregleda
		unique_id - unikatni identifikator testa (jedan test dobija isti unikatni ID i taj se prosleđuje svim metodama
		koje se bave izvršenjem testova)
		"""
		return self.gtest_testing_report_filename.format(test_name, unique_id)


	def get_status_report_path(self, dir_path, test_name, unique_id):
		"""
		Pomoćna metoda koja vraća putanju do fajla sa statusom pokretanja testa čiji je naziv dat

		Fajl sa statusom pokretanja je tekstualni fajl koji sadrži samo povratni kod koji je dobijen prilikom izvršenja
		testa

		dir_path - putanja na koju se postavljaju artefakti prilikom izvršenja testa
		test_name - naziv testa čiji se povratni kod pregleda
		unique_id - unikatni identifikator testa (jedan test dobija isti unikatni ID i taj se prosleđuje svim metodama
		koje se bave izvršenjem testova)
		"""
		gtest_status_name = self.gtest_testing_report_status_filename.format(test_name, unique_id)
		return os.path.join(dir_path, gtest_status_name)


	def get_parallel_testing_threads_count(self):
		return self.parallel_testing_threads_count


	def execute_test(self, test_name, execute_dir, executable_file_path, unique_id, report_path):
		logging.debug('Izvrsava se sledeci test: {0}'.format(test_name))
		result = {}

		gtest_status_path = self.get_status_report_path(execute_dir, test_name, unique_id)
		gtest_report_name = self.get_testing_report_filename(test_name, unique_id)

		# Brišu se fajlovi u koje će biti smešteni status pokretanja i rezultat izvršenja testa, kako bi se osiguralo da
		# neće biti upotrebljeni fajlovi od nekih prethodnih pokretanja:
		if os.path.isfile(gtest_status_path):
			os.unlink(gtest_status_path)
		if os.path.isfile(os.path.join(execute_dir, gtest_report_name)):
			os.unlink(os.path.join(execute_dir, gtest_report_name))

		command = self.execute_project_cmd.format(self.execution_timeout, executable_file_path, gtest_report_name,
												  test_name, report_path)
		logging.debug('Komanda za izvrsenje testova: {0}'.format(command))
		ret = call(command, shell=True, cwd=execute_dir)

		# Upis statusa izvršenja u fajl predviđen za to:
		with open(gtest_status_path, 'w') as f: 
			f.write(str(ret))


	def is_execution_report_created(self, dir_path, test_name, unique_id):
		return path.isfile(os.path.join(dir_path, self.get_testing_report_filename(test_name, unique_id)))


	def parse_testing_artefacts(self, test_name, dir_path, blocking_tests, unique_id):
		blocker = test_name in blocking_tests

		gtest_status_path = self.get_status_report_path(dir_path, test_name, unique_id)
		gtest_report_name = self.get_testing_report_filename(test_name, unique_id)

		# Očitavanje statusnog koda koji je dobijen prilikom izvršenja testa (nalazi se u posebnom tekstualnom fajlu):
		if not os.path.isfile(gtest_status_path):
			raise RuntimeError('''Nije uspelo izvrsenje testova - fajl sa statusom izvrsenja ({0}) nije pronadjen.
Ovo je interna greska, kontaktirati autora alata.'''.format(gtest_status_path))

		with open(gtest_status_path, 'r') as f: 
			status_str = f.read()

		try:
			status = int(status_str)
		except ValueError:
			raise RuntimeError('''Sadrzaj fajla sa statusom izvrsenja nije u skladu sa ocekivanim. Fajl: {0}
Ovo je interna greska, kontaktirati autora alata.'''.format(gtest_status_path))

		# Sistemski program "timeout" koji se koristi za pokretanje testova vraća kod 124 ukoliko je prekinuo predugo
		# izvršenje:
		if status == 0:
			pass # Tek treba da se odredi da li je test prošao ili ne, za sada se samo zna da je izvršenje prošlo

		elif status == 124:
			return SingleRunResult(name = test_name, result = 'timed-out', duration = float(self.execution_timeout),
								   blocker = blocker)

		# Ovde je obrađena malo komplikovanija situacija.
		# Ako je povratni kod 'timeout' komande 1 - onda ima dva podslučaja. 
		# Prvi, češći podslučaj je da to indikuje da je pokrenuti test pao.
		# Drugi, ređi podslučaj je da to indikuje nasilni prekid izvršenja testa, usled segfault-a ili slično. U tom slučaju, nema analize rezultata testa.
		
		elif (status == 1 and (not self.is_execution_report_created(dir_path, test_name, unique_id))) or status > 1:
			return SingleRunResult(name = test_name, result = 'crashed', duration = 0, blocker = blocker)

		# Učitavanje XML fajla sa rezultatom izvršenja, ako ima takvog fajla:

		filename = join(dir_path, gtest_report_name)
		error_message = '''Interna greska: format XML fajla sa rezultatima testiranja nije validan!
Fajl cije parsiranje nije uspelo: {0}'''.format(filename)

		if not os.path.isfile(filename):
			raise RuntimeError('''Nije uspelo izvrsenje testova - fajl sa izvestajem ({0}) nije pronadjen.
Ovo verovatno ukazuje na timeout prilikom izvrsenja.'''.format(filename))

		e = ElementTree.parse(filename).getroot()

		if e.tag != 'testsuites':
			raise RuntimeError(error_message)

		for suite in e:
			if not 'name' in suite.attrib:
				raise RuntimeError(error_message)

			suite_name = suite.attrib['name']
			for case in suite:
				blocker = False

				if case.tag != 'testcase':
					raise RuntimeError(error_message)
				if not 'name' in case.attrib:
					raise RuntimeError(error_message)
				if not 'status' in case.attrib:
					raise RuntimeError(error_message)

				name = '{0}.{1}'.format(suite_name, case.attrib['name'])

				# Proverava da li je definisano bodovanje za test koji je izvrsen:
				if name != test_name:
					util.fatal_error('Interna greska! Fajl sa izvestajem ne sadrzi rezultate odgovarajuceg testa.\n'
									 + 'Kontaktirati autora alata.')

				if case.attrib['status'] == 'run':
					if case.find('failure') is None:
						execution = 'passed'
					else:
						execution = 'failed'

				duration = float(case.attrib['time'])
				logging.debug('Rezultat pojedinacnog izvrsenja: name: {0}, result: {1}, duration: {2}, blocker: {3}'
							  .format(name, execution, duration, blocker))

				return SingleRunResult(name = test_name, result = execution, duration = duration, blocker = blocker)


	def get_test_names(self, autotest_path):
		with open (join(autotest_path, 'main.cpp'), 'r') as main_file:
			text = main_file.read();

		tests = self.test_names_regex.findall(text)

		results = []
		for t in tests:
			clean_ws = re.sub('[ \t]', '', t)
			full = re.sub('[,]', '.', clean_ws)
			results.append(full)

		return results


	def after_assignment_loaded(self, current_assignment_path, project_file_name):
		if self.launch_codeblocks_on_assignment_open:
			command = self.open_project_cmd.format(project_file_name)
			ret = call(command, shell=True, cwd=current_assignment_path)
			if ret != 0:
				raise RuntimeError('Nije uspelo otvaranje projekta koriscenjem Codeblocks!\n'
								   + 'Komanda koja je pokrenuta:\n{0}'.format(command))


	def before_build(self, dir_path):
		self.apply_replacements(self.assignment_build_replacements, dir_path)
