from collections import defaultdict
from Rule import Rule


class ERMiner:
    def __init__(self, path: str, min_sup: float = 0.5, min_con: float = 0.75):
        self.database_file: str = path
        self.db_size: int = 0
        self.min_sup: float = min_sup
        self.min_conf: float = min_con

        self.left_equivalence = defaultdict(list)
        self.right_equivalence = defaultdict(list)
        self.left_store = defaultdict(lambda: defaultdict(list))
        self.rules: list[Rule] = []

        # for every item, set of sequence ids where it occurs, eg. {1:{1, 2, 3}, 2:{1, 3, 4}...}
        self.sequence_ids = defaultdict(set)
        # for every item, dict seq id:first(last) occurrence, eg. {1:{1:1, 2:4, 3:2}, 2:{1:2}...}
        self.first_occurrences = defaultdict(dict)
        self.last_occurrences = defaultdict(dict)

    def run(self) -> None:
        self.read_database(self.database_file)
        self.find_rules()
        self.print_rules()

    def read_database(self, path: str) -> None:
        with open(path) as file:
            for i, line in enumerate(file):
                if line[0] != '-':
                    sequence = [set(map(int, transaction.split()))
                                for transaction in line.rstrip("-1 -2\n").split("-1")]
                    self.scan_sequence(sequence, i)
                self.db_size = i

    def scan_sequence(self, sequence: list[set[int]], sequence_id: int) -> None:
        for j, itemset in enumerate(sequence):
            for item in itemset:
                self.sequence_ids[item].add(sequence_id)
                self.last_occurrences[item].update({sequence_id: j})
                if sequence_id not in self.first_occurrences[item].keys():
                    self.first_occurrences[item].update({sequence_id: j})

    def find_rules(self) -> None:
        all_item_ids = list(self.sequence_ids)
        for last_i, i in enumerate(all_item_ids):
            for j in all_item_ids[last_i+1:]:
                common_sequences = self.sequence_ids[i] & self.sequence_ids[j]
                if len(common_sequences)/self.db_size >= self.min_sup:
                    sids_i_j, sids_j_i = self.find_rule_sequences(common_sequences, i, j)
                    self.build_equivalences(i, j, sids_i_j)
                    self.build_equivalences(j, i, sids_j_i)
        for left_class in self.left_equivalence:
            self.left_search(self.left_equivalence[left_class])
        for right_class in self.right_equivalence:
            self.right_search(self.right_equivalence[right_class])
        for left_class_size in self.left_store:
            for itemset in self.left_store[left_class_size]:
                self.left_search(self.left_store[left_class_size][itemset])

    def build_equivalences(self, antecedent: int, consequent: int, sids: set[int]) -> None:
        if (rule_support := len(sids) / self.db_size) >= self.min_sup:
            new_rule = Rule({antecedent}, {consequent}, round(rule_support, 3), sequences=sids,
                            antecedent_sequences=self.sequence_ids[antecedent])
            self.left_equivalence[antecedent].append(new_rule)
            self.right_equivalence[consequent].append(new_rule)
            self.check_rule_confidence(new_rule, self.sequence_ids[antecedent], sids)

    def check_rule_confidence(self, new_rule: Rule, sids_i: set[int], sids_i_j: set[int]) -> None:
        if (rule_confidence := len(sids_i_j) / len(sids_i)) >= self.min_conf:
            new_rule.confidence = round(rule_confidence, 3)
            self.rules.append(new_rule)

    def find_rule_sequences(self, common_sequences: set[int], i: int, j: int) -> tuple[set[int], set[int]]:
        sids_i_j = set()
        sids_j_i = set()
        for sequence in common_sequences:
            if self.first_occurrences[i][sequence] < self.last_occurrences[j][sequence]:
                sids_i_j.add(sequence)
            if self.first_occurrences[j][sequence] < self.last_occurrences[i][sequence]:
                sids_j_i.add(sequence)
        return sids_i_j, sids_j_i

    def left_search(self, left_equiv: list[Rule]) -> None:
        for i in range(len(left_equiv)):
            left_equiv_prim = []
            for j in range(i+1, len(left_equiv)):
                # uncommon_items = frozenset(left_equiv[i].consequent ^ left_equiv[j].consequent)
                # if not self.qualifies_to_pruning(uncommon_items):
                self.left_merge(left_equiv[i], left_equiv[j], left_equiv_prim)
            self.left_search(left_equiv_prim)

    # def qualifies_to_pruning(self, ab_set):
    #     return self.sparse_count_matrix[ab_set] / self.db_size < self.min_sup

    def left_merge(self, rule_s: Rule, rule_r: Rule, left_equiv: list[Rule]) -> None:
        rule_sequences = rule_s.sequences & rule_r.sequences
        if (rule_support := len(rule_sequences) / self.db_size) >= self.min_sup:
            new_rule = Rule(rule_s.antecedent, rule_s.consequent | rule_r.consequent, rule_support,
                            sequences=rule_sequences, antecedent_sequences=rule_s.antecedent_sequences)
            if (rule_confidence := len(rule_sequences) / len(rule_s.antecedent_sequences)) >= self.min_conf:
                new_rule.confidence = rule_confidence
                self.rules.append(new_rule)
            left_equiv.append(new_rule)

    def right_search(self, right_equiv: list[Rule]) -> None:
        for i in range(len(right_equiv)):
            right_equiv_prim = []
            for j in range(i+1, len(right_equiv)):
                # uncommon_items = frozenset(right_equiv[i].antecedent ^ right_equiv[j].antecedent)
                # if not self.qualifies_to_pruning(uncommon_items):
                self.right_merge(right_equiv[i], right_equiv[j], right_equiv_prim)
            self.right_search(right_equiv_prim)

    def right_merge(self, rule_s: Rule, rule_r: Rule, right_equiv: list[Rule]) -> None:
        rule_sequences = rule_s.sequences & rule_r.sequences
        if (rule_support := len(rule_sequences) / self.db_size) >= self.min_sup:
            antecedent_sequences = rule_s.antecedent_sequences & rule_r.antecedent_sequences
            new_rule = Rule(rule_s.antecedent | rule_r.antecedent, rule_s.consequent, rule_support,
                            sequences=rule_sequences, antecedent_sequences=antecedent_sequences)
            if (rule_confidence := len(rule_sequences) / len(antecedent_sequences)) >= self.min_conf:
                new_rule.confidence = rule_confidence
                self.rules.append(new_rule)
            right_equiv.append(new_rule)
            self.left_store[len(new_rule.antecedent)][frozenset(new_rule.antecedent)].append(new_rule)

    def print_rules(self) -> None:
        for rule in self.rules:
            print(rule)


if __name__ == "__main__":
    erminer = ERMiner("data/eshop.txt", 0.5, 0.75)
    erminer.run()
