"""
Paperwork configuration management code
"""

import ConfigParser
import os

import pyinsane.abstract_th as pyinsane


class _ScanTimes(object):
    __ITEM_2_CONFIG = {
        'calibration' : ('Scanner', 'ScanTimeCalibration'),
        'normal' : ('Scanner', 'ScanTime'),
        'ocr' : ('OCR', 'OCRTime'),
    }

    def __init__(self, config):
        self.__config = config

    def __getitem__(self, item):
        cfg = self.__ITEM_2_CONFIG[item]
        try:
            return float(self.__config._configparser.get(
                cfg[0], cfg[1]))
        except ConfigParser.NoOptionError:
            return 30.0

    def __setitem__(self, item, value):
        cfg = self.__ITEM_2_CONFIG[item]
        self.__config._configparser.set(cfg[0], cfg[1], str(value))


class PaperworkConfig(object):
    """
    Paperwork config. See each accessor to know for what purpose each value is
    used.
    """
    RECOMMENDED_RESOLUTION = 300
    CALIBRATION_RESOLUTION = 200

    def __init__(self):
        # values are stored directly in self._configparser
        self._configparser = ConfigParser.SafeConfigParser()
        self.scan_time = _ScanTimes(self)

        # Possible config files are evaluated in the order they are in the array.
        # The last one of the list is the default one.
        configfiles = [
            "./paperwork.conf",
            os.path.expanduser("~/.paperwork.conf"),
            ("%s/paperwork.conf"
             % (os.getenv("XDG_CONFIG_HOME",
                          os.path.expanduser("~/.config"))))
        ]

        configfile_found = False
        for self.__configfile in configfiles:
            if os.access(self.__configfile, os.R_OK):
                configfile_found = True
                print "Config file found: %s" % self.__configfile
                break
        if not configfile_found:
            print "Config file not found. Will use '%s'" % self.__configfile

    def read(self):
        """
        (Re)read the configuration.

        Beware that the current work directory may affect this operation:
        If there is a 'paperwork.conf' in the current directory, it will be
        read instead of '~/.paperwork.conf', see __init__())
        """
        # smash the previous config
        self._configparser = ConfigParser.SafeConfigParser()
        self._configparser.read([self.__configfile])

        # make sure that all the sections exist
        if not self._configparser.has_section("Global"):
            self._configparser.add_section("Global")
        if not self._configparser.has_section("OCR"):
            self._configparser.add_section("OCR")
        if not self._configparser.has_section("Scanner"):
            self._configparser.add_section("Scanner")
        if not self._configparser.has_section("GUI"):
            self._configparser.add_section("GUI")

    def __get_workdir(self):
        """
        Directory in which Paperwork must look for documents.
        Reminder: Documents are directories containing files called
        'paper.<X>.jpg', 'paper.<X>.txt' and possibly 'paper.<X>.words' ('<X>'
        being the page number).

        Returns:
            String.
        """
        try:
            return self._configparser.get("Global", "WorkDirectory")
        except ConfigParser.NoOptionError:
            return os.path.expanduser("~/papers")

    def __set_workdir(self, work_dir_str):
        """
        Set the work directory.
        """
        self._configparser.set("Global", "WorkDirectory", work_dir_str)

    workdir = property(__get_workdir, __set_workdir)

    def __get_ocrlang(self):
        """
        OCR lang. This the lang specified to the OCR. The string here in the
        configuration is identical to the one passed to the OCR tool on the
        command line.

        String.
        """
        try:
            return self._configparser.get("OCR", "Lang")
        except ConfigParser.NoOptionError:
            return "eng"

    def __set_ocrlang(self, lang):
        """
        Set the OCR lang
        """
        self._configparser.set("OCR", "Lang", lang)

    ocrlang = property(__get_ocrlang, __set_ocrlang)

    def __get_scanner_devid(self):
        """
        This is the id of the device selected by the user.

        String.
        """
        try:
            return self._configparser.get("Scanner", "Device")
        except ConfigParser.NoOptionError:
            return None

    def __set_scanner_devid(self, devid):
        """
        Set the device id selected by the user to use for scanning
        """
        self._configparser.set("Scanner", "Device", devid)

    scanner_devid = property(__get_scanner_devid, __set_scanner_devid)

    def __get_scanner_resolution(self):
        """
        This is the resolution of the scannner used for normal scans.

        String.
        """
        try:
            return int(self._configparser.get("Scanner", "Resolution"))
        except ConfigParser.NoOptionError:
            return self.RECOMMENDED_RESOLUTION

    def __set_scanner_resolution(self, resolution):
        """
        Set the scanner resolution used for normal scans.
        """
        self._configparser.set("Scanner", "Resolution", str(resolution))

    scanner_resolution = property(__get_scanner_resolution,
                                  __set_scanner_resolution)

    def __get_scanner_calibration(self):
        """
        This is the resolution of the scannner used for normal scans.

        String.
        """
        try:
            pt_a_x = int(self._configparser.get(
                "Scanner", "Calibration_Pt_A_X"))
            pt_a_y = int(self._configparser.get(
                "Scanner", "Calibration_Pt_A_Y"))
            pt_b_x = int(self._configparser.get(
                "Scanner", "Calibration_Pt_B_X"))
            pt_b_y = int(self._configparser.get(
                "Scanner", "Calibration_Pt_B_Y"))
            if (pt_a_x > pt_b_x):
                (pt_a_x, pt_b_x) = (pt_b_x, pt_a_x)
            if (pt_a_y > pt_b_y):
                (pt_a_y, pt_b_y) = (pt_b_y, pt_a_y)
            return ((pt_a_x, pt_a_y), (pt_b_x, pt_b_y))
        except ConfigParser.NoOptionError:
            # no calibration -> no cropping -> we have to keep the whole image
            # each time
            return None

    def __set_scanner_calibration(self, calibration):
        """
        Set the scanner resolution used for normal scans.
        """
        self._configparser.set("Scanner", "Calibration_Pt_A_X",
                                str(calibration[0][0]))
        self._configparser.set("Scanner", "Calibration_Pt_A_Y",
                                str(calibration[0][1]))
        self._configparser.set("Scanner", "Calibration_Pt_B_X",
                                str(calibration[1][0]))
        self._configparser.set("Scanner", "Calibration_Pt_B_Y",
                                str(calibration[1][1]))

    scanner_calibration = property(__get_scanner_calibration,
                                   __set_scanner_calibration)

    def __get_scanner_sources(self):
        """
        Indicates if the scanner source names

        Array of string
        """
        try:
            str_list = self._configparser.get("Scanner", "Sources")
            return str_list.split(",")
        except ConfigParser.NoOptionError:
            return []

    def __set_scanner_sources(self, sources):
        """
        Indicates if the scanner source names

        Array of string
        """
        str_list = ",".join(sources)
        self._configparser.set("Scanner", "Sources", str_list)

    scanner_sources = property(__get_scanner_sources, __set_scanner_sources)

    def get_scanner_inst(self):
        scanner = pyinsane.Scanner(self.scanner_devid)
        scanner.options['resolution'].value = self.scanner_resolution
        return scanner

    def __get_toolbar_visible(self):
        """
        Must the toolbar(s) be displayed ?

        Boolean.
        """
        try:
            val = int(self._configparser.get("GUI", "ToolbarVisible"))
            if val == 0:
                return False
            return True
        except ConfigParser.NoOptionError:
            return True

    def __set_toolbar_visible(self, visible):
        """
        Set the OCR lang
        """
        self._configparser.set("GUI", "ToolbarVisible", str(int(visible)))

    toolbar_visible = property(__get_toolbar_visible, __set_toolbar_visible)


    def write(self):
        """
        Rewrite the configuration file. It rewrites the same file than
        PaperworkConfig.read() read.
        """
        file_path = self.__configfile
        print "Writing %s ... " % file_path
        with open(file_path, 'wb') as file_descriptor:
            self._configparser.write(file_descriptor)
        print "Done"
