#    Paperwork - Using OCR to grep dead trees the easy way
#    Copyright (C) 2012  Jerome Flesch
#
#    Paperwork is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Paperwork is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Paperwork.  If not, see <http://www.gnu.org/licenses/>.

import gettext
import gio
import poppler

from paperwork.backend.pdf.doc import PdfDoc
from paperwork.backend.img.doc import ImgDoc

_ = gettext.gettext


class SinglePdfImporter(object):
    def __init__(self):
        pass

    def can_import(self, file_uri, current_doc=None):
        return file_uri.lower().endswith(".pdf")

    def import_doc(self, file_uri, config, docsearch, current_doc=None):
        doc = PdfDoc(config.workdir)
        doc.import_pdf(config, file_uri)
        for page in doc.pages:
            docsearch.index_page(page)
        return (doc, doc.pages[0])

    def __str__(self):
        return _("Import PDF")


class MultiplePdfImporter(object):
    def __init__(self):
        pass

    def __get_all_children(self, parent):
        children = parent.enumerate_children(
                attributes=gio.FILE_ATTRIBUTE_STANDARD_NAME,
                flags=gio.FILE_QUERY_INFO_NOFOLLOW_SYMLINKS)
        for child in children:
            name = child.get_attribute_as_string(
                    gio.FILE_ATTRIBUTE_STANDARD_NAME)
            child = parent.get_child(name)
            try:
                for child in self.__get_all_children(child):
                    yield child
            except gio.Error:
                yield child

    def can_import(self, file_uri, current_doc=None):
        try:
            parent = gio.File(file_uri)
            for child in self.__get_all_children(parent):
                if child.get_basename().lower().endswith(".pdf"):
                    return True
        except gio.Error:
            pass
        return False

    def import_doc(self, file_uri, config, docsearch, current_doc=None):
        parent = gio.File(file_uri)
        doc = None

        idx = 0

        for child in self.__get_all_children(parent):
            if not child.get_basename().lower().endswith(".pdf"):
                continue
            try:
                # make sure we can import it
                poppler.document_new_from_file(child.get_uri(),
                                               password=None)
            except Exception:
                continue
            doc = PdfDoc(config.workdir)
            doc.path += ("_%02d" % idx)
            doc.docid += ("_%02d" % idx)
            doc.import_pdf(config, child.get_uri())
            for page in doc.pages:
                docsearch.index_page(page)
            idx += 1

        assert(doc != None)
        return (doc, doc.pages[0])

    def __str__(self):
        return _("Import each PDF in the folder as a new document")


class SingleImageImporter(object):
    def __init__(self):
        pass

    def can_import(self, file_uri, current_doc=None):
        for ext in ImgDoc.IMPORT_IMG_EXTENSIONS:
            if file_uri.lower().endswith(ext):
                return True
        return False

    def import_doc(self, file_uri, config, docsearch, current_doc=None):
        if current_doc == None:
            current_doc = ImgDoc(config.workdir)
        current_doc.import_image(file_uri, config.ocrlang)
        page = current_doc.pages[current_doc.nb_pages-1]
        docsearch.index_page(page)
        return (current_doc, page)

    def __str__(self):
        return _("Append the image to the current document")


IMPORTERS = [
    SinglePdfImporter(),
    SingleImageImporter(),
    MultiplePdfImporter(),
]

def get_possible_importers(file_uri, current_doc=None):
    importers = []
    for importer in IMPORTERS:
        if importer.can_import(file_uri, current_doc):
            importers.append(importer)
    return importers
