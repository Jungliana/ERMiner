from collections import defaultdict
from copy import copy
from Rule import Rule


class RuleGrowth:
    def __init__(self, file_path: str, minsup: float = 0.75, mincon: float = 0.5):
        self.database: list[list[set[int]]] = self.read_database(file_path)
        self.db_size: int = len(self.database)
        self.min_sup: float = minsup
        self.min_conf: float = mincon
        self.rules: list[Rule] = []

        # for every item, set of sequence ids where it occurs, eg. {1:{1, 2, 3}, 2:{1, 3, 4}...}
        self.sequence_ids = defaultdict(set)
        # for every item, dict seq id:first(last) occurrence, eg. {1:{1:1, 2:4, 3:2}, 2:{1:2}...}
        self.first_occurrences = defaultdict(dict)
        self.last_occurrences = defaultdict(dict)

    @staticmethod
    def read_database(file_path: str) -> list[list[set[int]]]:
        sequences = []
        with open(file_path) as file:
            for line in file:
                if line[0] != '-':
                    sequences.append([set(map(int, transaction.split()))
                                      for transaction in line.rstrip("-1 -2\n").split("-1")])
        return sequences

    def run(self) -> None:
        self.scan_database()
        self.find_rules()
        self.print_rules()

    def scan_database(self) -> None:
        for i, sequence in enumerate(self.database):
            for j, itemset in enumerate(sequence):
                for item in itemset:
                    self.sequence_ids[item].add(i)
                    self.last_occurrences[item].update({i: j})
                    if i not in self.first_occurrences[item].keys():
                        self.first_occurrences[item].update({i: j})

    def find_rules(self) -> None:
        all_item_ids = list(self.sequence_ids)
        for i in all_item_ids:
            for j in all_item_ids[i+1:]:
                common_sequences = self.sequence_ids[i] & self.sequence_ids[j]
                if len(common_sequences)/self.db_size >= self.min_sup:
                    sids_i_j, sids_j_i = self.find_rule_sequences(common_sequences, i, j)
                    self.expand(antecedent=i, consequent=j, sids=sids_i_j)
                    self.expand(antecedent=j, consequent=i, sids=sids_j_i)

    def find_rule_sequences(self, common_sequences, i, j) -> tuple[set[int], set[int]]:
        sids_i_j = set()
        sids_j_i = set()
        for sequence in common_sequences:
            if self.first_occurrences[i][sequence] < self.last_occurrences[j][sequence]:
                sids_i_j.add(sequence)
            if self.first_occurrences[j][sequence] < self.last_occurrences[i][sequence]:
                sids_j_i.add(sequence)
        return sids_i_j, sids_j_i

    def expand(self, antecedent: int, consequent: int, sids: set[int]) -> None:
        if (rule_support := len(sids) / self.db_size) >= self.min_sup:
            new_rule = Rule({antecedent}, {consequent}, round(rule_support, 3))
            self.expand_left(rule_i_j=new_rule, sids_i=self.sequence_ids[antecedent],
                             sids_i_j=sids, last_occurrences_j=self.last_occurrences[consequent])
            self.expand_right(rule_i_j=new_rule, sids_i=self.sequence_ids[antecedent],
                              sids_j=self.sequence_ids[consequent],
                              sids_i_j=sids, first_occurrences_i=self.first_occurrences[antecedent],
                              last_occurrences_j=self.last_occurrences[consequent])
            self.check_rule_confidence(new_rule, self.sequence_ids[antecedent], sids)

    def expand_left(self, rule_i_j: Rule, sids_i: set,
                    sids_i_j: set, last_occurrences_j: dict) -> None:
        sids_c = self.find_items_to_left_expand(list(sids_i_j), last_occurrences_j, max(rule_i_j.antecedent))
        for c in sids_c:
            if (rule_support := len(sids_c[c])/self.db_size) >= self.min_sup:
                sids_ic = sids_c[c] & sids_i
                rule_ic_j = Rule(rule_i_j.antecedent | {c}, rule_i_j.consequent, round(rule_support, 3))
                self.expand_left(rule_i_j=rule_ic_j, sids_i=sids_ic,
                                 sids_i_j=sids_c[c], last_occurrences_j=last_occurrences_j)
                self.check_rule_confidence(rule_ic_j, sids_i=sids_ic, sids_i_j=sids_c[c])

    def find_items_to_left_expand(self, sequence_ids: list[int], last_occurrences: dict, max_item: int) -> dict:
        """
        For each sid ∈ sidsI->J, scan the sequence sid from the first itemset to the itemset before
        the last occurrence of J. For each item c appearing in these sequences that is lexically larger
        than items in I, record in a variable sidsIc->J the sids of the sequences where c is found.
        """
        sequence_ids_c = defaultdict(set)
        for sid in sequence_ids:
            for i in range(last_occurrences[sid]):
                for item in self.database[sid][i]:
                    if item > max_item:
                        sequence_ids_c[item].add(sid)
        return sequence_ids_c

    def expand_right(self, rule_i_j: Rule, sids_i: set, sids_j: set, sids_i_j: set,
                     first_occurrences_i: dict, last_occurrences_j: dict) -> None:
        sids_c = self.find_items_to_right_expand(list(sids_i_j), first_occurrences_i, max(rule_i_j.consequent))
        for c in sids_c:
            if (rule_support := len(sids_c[c])/self.db_size) >= self.min_sup:
                sids_jc = sids_c[c] & sids_j
                last_occurrences_jc = self.update_last_occurrences(last_occurrences_j, c, sids_jc)
                rule_i_jc = Rule(rule_i_j.antecedent, rule_i_j.consequent | {c}, round(rule_support, 3))
                self.expand_left(rule_i_j=rule_i_jc, sids_i=sids_i,
                                 sids_i_j=sids_c[c], last_occurrences_j=last_occurrences_jc)
                self.expand_right(rule_i_j=rule_i_jc, sids_i=sids_i, sids_j=sids_j,
                                  sids_i_j=sids_c[c], first_occurrences_i=first_occurrences_i,
                                  last_occurrences_j=last_occurrences_jc)
                self.check_rule_confidence(rule_i_jc, sids_i=sids_i, sids_i_j=sids_c[c])

    def find_items_to_right_expand(self, sequence_ids: list[int], first_occurrences: dict, max_item: int) -> dict:
        """
        For each sid ∈ sidsI->J, scan the sequence sid from the itemset after the first occurrence of I
        to the last itemset. For each item c appearing in these sequences that is lexically larger than
        items in J, record in a variable sidsI->Jc the sids of the sequences where c is found.
        """
        sequence_ids_c = defaultdict(set)
        for sid in sequence_ids:
            for i in range(first_occurrences[sid]+1, len(self.database[sid])):
                for item in self.database[sid][i]:
                    if item > max_item:
                        sequence_ids_c[item].add(sid)
        return sequence_ids_c

    def update_last_occurrences(self, last_occurrences_j: dict[int], c: int, sids_jc: set) -> dict[int]:
        last_occurrences_jc = copy(last_occurrences_j)
        for sid in sids_jc:
            for j, itemset in enumerate(self.database[sid]):
                if c in itemset and j < last_occurrences_jc[sid]:
                    last_occurrences_jc.update({sid: j})
        return last_occurrences_jc

    def check_rule_confidence(self, new_rule, sids_i, sids_i_j) -> None:
        if (rule_confidence := len(sids_i_j) / len(sids_i)) >= self.min_conf:
            new_rule.confidence = round(rule_confidence, 3)
            self.rules.append(new_rule)

    def print_rules(self) -> None:
        for rule in self.rules:
            print(rule)


if __name__ == "__main__":
    rulegrowth = RuleGrowth("data/example.txt", 0.5, 0.75)
    rulegrowth.run()
