from collections import defaultdict
from Rule import Rule


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
        self.db_size = len(self.database)
        self.min_sup = minsup
        self.min_conf = mincon
        self.left_store = []
        self.rules = []
        self.sparse_count_matrix = defaultdict(int)

        self.sequence_ids = defaultdict(set)  # for every item, set of sequence ids where it occurs, eg. {1:{1, 2, 3}, 2:{1, 3, 4}...}
        self.first_occurrences = defaultdict(dict)  # for every item, dict seq id:first occurrence, eg. {1:{1:1, 2:4, 3:2}, 2:{1:2}...}
        self.last_occurrences = defaultdict(dict)

    def run(self):
        pass

    def build_sparse_count_matrix(self):
        all_items = list(self.sequence_ids.keys())
        for i, item_a in enumerate(all_items):
            for j in range(i+1, len(all_items)):
                common_sequences = self.sequence_ids[item_a] & self.sequence_ids[all_items[j]]
                self.sparse_count_matrix.update({frozenset({item_a, all_items[j]}): len(common_sequences)})

    def scan_database(self) -> None:
        for i, sequence in enumerate(self.database):
            for j, itemset in enumerate(sequence):
                for item in itemset:
                    self.sequence_ids[item].add(i)
                    self.last_occurrences[item].update({i: j})
                    if i not in self.first_occurrences[item].keys():
                        self.first_occurrences[item].update({i: j})
        self.build_sparse_count_matrix()

    def remove_items_with_low_support(self) -> None:
        to_remove = []
        for item in self.sequence_ids:
            if len(self.sequence_ids[item])/self.db_size < self.min_sup:
                to_remove.append(item)
        for item in to_remove:
            del self.sequence_ids[item]
            del self.first_occurrences[item]
            del self.last_occurrences[item]

    def find_1_1_rules(self):
        for i in self.sequence_ids:
            for j in self.sequence_ids:
                if i != j:
                    common_sequences = self.sequence_ids[i] & self.sequence_ids[j]
                    if len(common_sequences)/self.db_size >= self.min_sup:
                        for sequence in common_sequences:
                            if self.first_occurrences[i][sequence] < self.last_occurrences[j][sequence]:
                                self.rules.append(Rule(antecedent=self.sequence_ids[i], consequent=self.sequence_ids[j]))


def left_search(left_equiv, rules):
    pass


def right_search(right_equiv, rules):
    pass


if __name__ == "__main__":
    data = read_database("data/example.txt")
    erminer = ERMiner(data, 0.5, 0.75)
    erminer.scan_database()
    erminer.build_sparse_count_matrix()
    erminer.find_1_1_rules()
    pass