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


class RuleGrowth:
    def __init__(self, database: list[list[set[int]]], minsup: float = 0.75, mincon: float = 0.5):
        self.database: list[list[set[int]]] = database
        self.db_size: int = len(self.database)
        self.min_sup: float = minsup
        self.min_conf: float = mincon
        self.rules: list[Rule] = []

        # for every item, set of sequence ids where it occurs, eg. {1:{1, 2, 3}, 2:{1, 3, 4}...}
        self.sequence_ids = defaultdict(set)
        # for every item, dict seq id:first(last) occurrence, eg. {1:{1:1, 2:4, 3:2}, 2:{1:2}...}
        self.first_occurrences = defaultdict(dict)
        self.last_occurrences = defaultdict(dict)

    def print_rules(self) -> None:
        for rule in self.rules:
            print(rule)

    def scan_database(self) -> None:
        for i, sequence in enumerate(self.database):
            for j, itemset in enumerate(sequence):
                for item in itemset:
                    self.sequence_ids[item].add(i)
                    self.last_occurrences[item].update({i: j})
                    if i not in self.first_occurrences[item].keys():
                        self.first_occurrences[item].update({i: j})

    def remove_items_with_low_support(self) -> None:
        to_remove = []
        for item in self.sequence_ids:
            if len(self.sequence_ids[item])/self.db_size < self.min_sup:
                to_remove.append(item)
        for item in to_remove:
            del self.sequence_ids[item]
            del self.first_occurrences[item]
            del self.last_occurrences[item]

    def find_rules(self):
        all_item_ids = list(self.sequence_ids)
        for i in all_item_ids:
            for j in all_item_ids[i+1:]:
                common_sequences = self.sequence_ids[i] & self.sequence_ids[j]
                if len(common_sequences)/self.db_size >= self.min_sup:
                    sids_i_j, sids_j_i = self.find_rule_sequences(common_sequences, i, j)
                    if (rule_support := len(sids_i_j)/self.db_size) >= self.min_sup:
                        new_rule = Rule({i}, {j}, rule_support)
                        self.expand_left(rule_i_j=new_rule, sids_i=self.sequence_ids[i],
                                         sids_i_j=sids_i_j, last_occurrences_j=self.last_occurrences[j])
                        # self.expand_right()
                        self.rules.append(new_rule)

    def find_rule_sequences(self, common_sequences, i, j):
        sids_i_j = set()
        sids_j_i = set()
        for sequence in common_sequences:
            if self.first_occurrences[i][sequence] < self.last_occurrences[j][sequence]:
                sids_i_j.add(sequence)
            if self.first_occurrences[j][sequence] < self.last_occurrences[i][sequence]:
                sids_j_i.add(sequence)
        return sids_i_j, sids_j_i

    def find_items_to_expand(self, sequence_ids: list[int], last_occurrences: dict, max_item: int) -> dict:
        sequence_ids_c = defaultdict(set)
        for sid in sequence_ids:
            for i in range(last_occurrences[sid]):
                for item in self.database[sid][i]:
                    if item > max_item:
                        sequence_ids_c[item].add(sid)
        return sequence_ids_c

    def expand_left(self, rule_i_j: Rule, sids_i: set,
                    sids_i_j: set, last_occurrences_j: dict) -> None:
        # rule, eg. ({a, b}, {c})
        # sids I, eg. {1, 2, 5}
        # sids I->J, eg. {1, 5}
        # last occurrences J, eg. {1:3, 2:5, 7:2}
        sids_c = self.find_items_to_expand(list(sids_i_j), last_occurrences_j, max(rule_i_j.antecedent))
        for c in sids_c:
            if (rule_support := len(sids_c[c])/self.db_size) >= self.min_sup:
                sids_i_c = sids_c[c] & sids_i
                rule_ic_j = Rule(rule_i_j.antecedent | {c}, rule_i_j.consequent, rule_support)
                self.expand_left(rule_i_j=rule_ic_j, sids_i=sids_i_c,
                                 sids_i_j=sids_c[c], last_occurrences_j=last_occurrences_j)
                self.rules.append(rule_ic_j)

    def expand_right(self):
        pass

    def run(self):
        self.scan_database()
        self.find_rules()


if __name__ == "__main__":
    data = read_database("data/example.txt")
    rulegrowth = RuleGrowth(data, 0.5, 0.75)
    rulegrowth.run()
    rulegrowth.print_rules()
    pass
