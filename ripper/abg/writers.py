import csv

class Writer:
    def __init__(self):
        self.headers=None


class CSV_Writer(Writer):

    def __init__(self, output):
        self.writer=csv.DictWriter(output, ["stupid"])
        self.headers=None

    def addHeaders(self, keys):
        self.writer.fieldnames=keys
        self.writer.writeheader()
        self.headers=keys


    def addRow(self, row = {}):
        if (self.headers == None):
            self.addHeaders(row.keys())
        self.writer.writerow(row)
