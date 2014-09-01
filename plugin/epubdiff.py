__author__ = 'nic'


import difflib
import zipfile
import os
import hashlib



class EpubDiffError (Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class EpubDiff (object):



    def __init__(self, original, modified):

        self.TEXTCHARS = ''.join(map(chr, [7,8,9,10,12,13,27] + range(0x20, 0x100)))
        self.ALLBYTES = ''.join(map(chr, range(256)))

        self.changelist = [
            (0, 'No Change'),
            (1, 'File Removed'),
            (2, 'File Added'),
            (3, 'Binary File Change'),
            (4, 'Text File Change (With Diff)'),
            (5, 'Text File Change (Without Diff)'),
        ]

        if os.path.exists(original) and os.path.exists(modified):
            if zipfile.is_zipfile(original) and zipfile.is_zipfile(modified):
                self.original = zipfile.ZipFile(original)
                self.modified = zipfile.ZipFile(modified)
            else:
                raise EpubDiffError("One or more files are not Epub/Zip files")
        else:
            raise EpubDiffError("One or more files do not exist")

        self.doclist = [(self.original, 0), (self.modified, 1)]
        self.manifest = {}
        self.difflog = []

    def check(self):
        self.buildmanifest()
        self.checkbinary()
        self.getchecksums()
        self.checkdiff()
        self.getdiff()
        self.builddifflog()

    def buildmanifest(self):
        for document, docID in self.doclist:
            for item in document.namelist():
                if item in self.manifest.keys():
                    self.manifest[item][docID] = True
                else:
                    self.manifest[item] = [False, False, False, False]
                    self.manifest[item][docID] = True

    def checkbinary(self):
        for path, info in self.manifest.iteritems():
            if info[0]:
                o_binary = bool(self.original.read(path).translate(self.ALLBYTES, self.TEXTCHARS))
                self.manifest[path][2] = o_binary
            if info[1]:
                m_binary = bool(self.modified.read(path).translate(self.ALLBYTES, self.TEXTCHARS))
                self.manifest[path][3] = m_binary


    def getchecksums(self):
        for path, info in self.manifest.iteritems():
            if info[0] and info[1]:
                o_md5 = hashlib.new('md5')
                m_md5 = hashlib.new('md5')

                o_md5.update(self.original.read(path))
                m_md5.update(self.modified.read(path))

                self.manifest[path].append(o_md5.hexdigest())
                self.manifest[path].append(m_md5.hexdigest())

                del o_md5, m_md5

    def checkdiff (self):
        for path, info in self.manifest.iteritems():
            if info[0] and info[1]:
                self.manifest[path].append(False)
                if not info[4] == info[5]:
                    self.manifest[path][6] = True

    def getdiff(self):
        for path, info in self.manifest.iteritems():
            if info[0] and info[1] and (not info[2]) and (not info[3]) and info[6]:
                diff = difflib.unified_diff(self.original.read(path).splitlines(), self.modified.read(path).splitlines())
                self.manifest[path].append('\n'.join(list(diff)))

    def builddifflog(self):
        for path, info in self.manifest.iteritems():
            if not info[1]:
                self.difflog.append((self.changelist[1], path))

            if not info[0]:
                self.difflog.append((self.changelist[2], path))

            if info[0] and info[1] and info[2] and info[3] and info[6]:
                self.difflog.append((self.changelist[3], path, info[4], info[5]))

            if info[0] and info[1] and (not info[2]) and (not info[3]) and info[6] and info[7]:
                self.difflog.append((self.changelist[4], path, info[4], info[5], info[7]))


            if info[0] and info[1] and (not info[2]) and (not info[3]) and info[6] and (not info[7]):
                self.difflog.append((self.changelist[5], path, info[4], info[5]))


