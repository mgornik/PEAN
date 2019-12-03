# -*- coding: utf-8 -*-

import json
import os

from os.path import join

class Configuration:
	"""
	Globalna konfiguracija alata
	"""

	def load_configuration(self, file_name):
		"""
		Učitavanje fajla pod zadatim nazivom, sa globalnom konfiguracijom alata

		Globalna konfiguracija alata je konfiguracija koja ne zavisi od izabranog back-end-a.
		Fajl se traži na putanji na kojoj se nalazi i sam alat.

		file_name - naziv fajla sa globalnom konfiguracijom alata
		"""
		dir = os.path.dirname(__file__)
		with open(os.path.join(dir, file_name)) as data_file:    
			data = json.load(data_file)

		self.GROUP1_DIR = data['Group1Path']
		self.GROUP2_DIR = data['Group2Path']
		self.TEMP_PATH = data['TempPath']
		self.ASSIGNMENTS_ARCHIVE_PATTERN = data['AssignmentsArchivePattern']
		self.SINGLE_ASSIGNMENT_ARCHIVE_EXT = data['SingleAssignmentArchiveExt']
		self.SINGLE_ASSIGNMENT_ARCHIVE_PATTERN = data['SingleAssignmentArchivePattern']
		self.STUDENTS_LIST_PATTERN = data['StudentsListPattern']
		self.TIMEOUT = data['Timeout']
		self.RATING_CRITERIA_FILENAME = data['RatingConfigFilename']
		self.FINAL_REPORT_FILENAME = data['FinalReportFilename']
		self.FINAL_REPORT_XSLT_FILENAME = data['FinalReportXSLTFilename']
		self.EXPORTED_REPORT_FILENAME = data['ExportedReportFilename']
		self.EXPORTED_ARCHIVE_FILENAME = data['ExportedArchiveFilename']
		self.COMMENT_FILENAME = data['CommentFilename']
		self.STATION_FILENAME = data['StationFilename']
		self.ARCHIVE_PATH = data['ArchivePath']
		self.ASSIGNMENTS_PATH = data['AssignmentsPath']
		self.REPORTS_PATH = data['ReportsPath']
		self.CONSOLE_REPORT_FILENAME = data['ConsoleReportFilename']
		self.ALTERED_ASSIGNMENTS_PATH = data['AlteredAssignmentsPath']
		self.CURRENT_ASSIGNMENT_PATH = data['CurrentAssignmentPath']
		self.CURRENT_ALT_ASSIGNMENT_PATH = data['CurrentAltAssignmentPath']
		self.BACKUP_PATH = data['BackupPath']
		self.INITIAL_PROJECT_PATH = data['InitialProjectPath']
		self.AUTOTEST_PATH = data['AutotestPath']
		self.EXTRACT_ASSIGNMENTS_CMD = data['ExtractAssignmentsCommand']
		self.EXTRACT_SINGLE_ASSIGNMENT_CMD = data['ExtractSingleAssignmentCommand']
		self.COMPRESS_REPORT_COMMAND = data['CompressReportCommand'].format(self.EXPORTED_ARCHIVE_FILENAME,
																			self.EXPORTED_REPORT_FILENAME)
		self.VISUAL_DIFF_CMD = data['VisualDiffCommand']
		self.TEXT_EDIT_CMD = data['TextEditCommand'] + ' &'

		self.AUTOBUILD_PATH = join(self.CURRENT_ASSIGNMENT_PATH, 'autobuild')
		self.ALT_AUTOBUILD_PATH = join(self.CURRENT_ALT_ASSIGNMENT_PATH, 'autobuild')
