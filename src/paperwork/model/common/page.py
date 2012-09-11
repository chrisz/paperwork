import codecs
from copy import copy
import Image
import os
import os.path
import re

from paperwork.util import split_words


class PageExporter(object):
    can_change_quality = True

    def __init__(self, page, img_format='PNG', mime='image/png',
                 valid_exts=['png']):
        self.page = page
        self.img_format = img_format
        self.mime = mime
        self.valid_exts = valid_exts
        self.__quality = 75
        self.__img = None

    def get_mime_type(self):
        return self.mime

    def get_file_extensions(self):
        return self.valid_exts

    def save(self, target_path):
        # the user gives us a quality between 0 and 100
        # but PIL expects a quality between 1 and 75
        quality = int(float(self.__quality) / 100.0 * 74.0) + 1
        # We also adjust the size of the image
        resize_factor = float(self.__quality) / 100.0

        img = self.page.img

        new_size = (int(resize_factor * img.size[0]),
                    int(resize_factor * img.size[1]))
        img = img.resize(new_size, Image.ANTIALIAS)

        img.save(target_path, self.img_format, quality=quality)
        return target_path

    def refresh(self):
        tmp = "%s.%s" % (os.tempnam(None, "paperwork_export_"),
                         self.valid_exts[0])
        path = self.save(tmp)
        img = Image.open(path)
        img.load()

        self.__img = (path, img)

    def set_quality(self, quality):
        self.__quality = int(quality)
        self.__img = None

    def estimate_size(self):
        if self.__img == None:
            self.refresh()
        return os.path.getsize(self.__img[0])

    def get_img(self):
        if self.__img == None:
            self.refresh()
        return self.__img[1]

    def __str__(self):
        return self.img_format

    def __copy__(self):
        return PageExporter(self.page, self.img_format, self.mime,
                           self.valid_exts)


class BasicPage(object):
    SCAN_STEP_SCAN = "scanning"
    SCAN_STEP_OCR = "ocr"

    text = ""
    boxes = []
    img = None

    def __init__(self, doc, page_nb):
        """
        Don't create directly. Please use ImgDoc.get_page()
        """
        self.doc = doc
        self.page_nb = page_nb
        assert(self.page_nb >= 0)
        self.__prototype_exporters = {
            'PNG' : PageExporter(self, 'PNG', 'image/png', ["png"]),
            'JPEG' : PageExporter(self, 'JPEG', 'image/jpeg', ["jpeg", "jpg"]),
        }

    def get_thumbnail(self, width):
        raise NotImplementedError()

    def print_page_cb(self, print_op, print_context):
        raise NotImplementedError()

    def redo_ocr(self, ocrlang):
        raise NotImplementedError()

    def destroy(self):
        raise NotImplementedError()

    def get_boxes(self, sentence):
        """
        Get all the boxes corresponding the given sentence

        Arguments:
            sentence --- can be string (will be splited), or an array of strings
        Returns:
            an array of boxes (see pyocr boxes)
        """
        if isinstance(sentence, unicode):
            keywords = split_words(sentence)
        else:
            assert(isinstance(sentence, list))
            keywords = sentence

        output = []
        for keyword in keywords:
            for box in self.boxes:
                # unfold generator output
                words = [x for x in split_words(box.content)]
                if keyword in words:
                    output.append(box)
        return output

    def get_export_formats(self):
        return self.__prototype_exporters.keys()

    def build_exporter(self, file_format='PNG'):
        return copy(self.__prototype_exporters[file_format.upper()])

    def __str__(self):
        return "%s p%d" % (str(self.doc), self.page_nb + 1)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        if None == other:
            return False
        return self.doc == other.doc and self.page_nb == other.page_nb

    def __get_keywords(self):
        """
        Get all the keywords related of this page

        Returns:
            An array of strings
        """
        for line in self.text:
            for word in split_words(line):
                yield(word)

    keywords = property(__get_keywords)

