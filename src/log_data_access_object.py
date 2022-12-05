class LogDataAccessObject:

    def __init__(self, array, dict):
        # array for preserving the "index term" pairs.
        self.ordered_logs = array
        # dictionary for the operations linked to the "index term" pairs.
        self.term_indexed_logs = dict
