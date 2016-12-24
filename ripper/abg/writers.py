import csv

class Writer:
    def __init__(self):
        self.headers=None


class CSV_Writer(Writer):

    def __init__(self, output):
        self.writer=csv.DictWriter(output, fieldnames=["match-id","id","name","player2-name","group-stages-enabled","player1-name","match-completed-at","state","match-state","completed-at","match-scores-csv","created-at", "DQ", "DQ_text"])
        self.headers = None

    def addRow(self, row = {}):
        if (self.headers == None):
            self.writer.writeheader()
            self.headers = True
        self.writer.writerow(row)
