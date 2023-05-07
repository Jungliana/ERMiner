from collections import defaultdict


def read_database(path: str) -> list[list[set[int]]]:
    sequences = []
    with open(path) as file:
        for line in file:
            if line[0] != '-':
                sequences.append([set(map(int, transaction.split()))
                                  for transaction in line.rstrip("-1 -2\n").split("-1")])
    return sequences


class ERMiner:
    def __init__(self, database, minsup, mincon):
        self.database = database
        self.min_sup = minsup
        self.min_conf = mincon
        self.left_store = []
        self.rules = []

        self.sequence_ids = defaultdict(set)  # for every item, set of sequence ids where it occurs, eg. {1:{1, 2, 3}, 2:{1, 3, 4}...}
        self.first_occurrences = defaultdict(dict)  # for every item, dict seq id:first occurrence, eg. {1:{1:1, 2:4, 3:2}, 2:{1:2}...}
        self.last_occurrences = defaultdict(dict)

    def run(self):
        pass

    def scan_database(self) -> None:
        for i, sequence in enumerate(self.database):
            for j, itemset in enumerate(sequence):
                for item in itemset:
                    self.sequence_ids[item].add(i)
                    self.last_occurrences[item].update({i: j})
                    if i not in self.first_occurrences[item].keys():
                        self.first_occurrences[item].update({i: j})


def left_search(left_equiv, rules):
    pass


def right_search(right_equiv, rules):
    pass


if __name__ == "__main__":
    data = read_database("data/example.txt")
    erminer = ERMiner(data, 0.75, 0.75)
    erminer.scan_database()
