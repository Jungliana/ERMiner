from collections import defaultdict
from Rule import Rule


class ERMiner:
    def __init__(self, path: str, minsup: float = 0.5, mincon: float = 0.75):
        self.database_file: str = path
        self.db_size: int = 0
        self.min_sup: float = minsup
        self.min_conf: float = mincon

        self.left_equivalence = defaultdict(list)
        self.right_equivalence = defaultdict(list)
        self.left_store = defaultdict(list)
        self.rules: list[Rule] = []
        self.sparse_count_matrix = defaultdict(int)

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

    def scan_sequence(self, sequence, sequence_id) -> None:
        for j, itemset in enumerate(sequence):
            for item in itemset:
                self.sequence_ids[item].add(sequence_id)
                self.last_occurrences[item].update({sequence_id: j})
                if sequence_id not in self.first_occurrences[item].keys():
                    self.first_occurrences[item].update({sequence_id: j})
        self.build_sparse_count_matrix()

    def build_sparse_count_matrix(self):
        all_items = list(self.sequence_ids.keys())
        for i, item_a in enumerate(all_items):
            for j in range(i+1, len(all_items)):
                common_sequences = self.sequence_ids[item_a] & self.sequence_ids[all_items[j]]
                self.sparse_count_matrix.update({frozenset({item_a, all_items[j]}): len(common_sequences)})

    def find_rules(self):
        all_item_ids = list(self.sequence_ids)
        for i in all_item_ids:
            for j in all_item_ids[i+1:]:
                common_sequences = self.sequence_ids[i] & self.sequence_ids[j]
                if len(common_sequences)/self.db_size >= self.min_sup:
                    sids_i_j, sids_j_i = self.find_rule_sequences(common_sequences, i, j)
                    self.build_equivalences(i, j, sids_i_j)
                    self.build_equivalences(j, i, sids_j_i)
        for left_class in self.left_equivalence:
            self.left_search(left_class)
        for right_class in self.right_equivalence:
            self.right_search(right_class)
        for left_class_size in self.left_store:
            for itemset in left_class_size:
                self.left_search(itemset)

    def build_equivalences(self, antecedent, consequent, sids):
        if (rule_support := len(sids) / self.db_size) >= self.min_sup:
            new_rule = Rule({antecedent}, {consequent}, round(rule_support, 3))
            self.left_equivalence[antecedent].append(new_rule)
            self.right_equivalence[consequent].append(new_rule)
            self.check_rule_confidence(new_rule, self.sequence_ids[antecedent], sids)

    def check_rule_confidence(self, new_rule, sids_i, sids_i_j) -> None:
        if (rule_confidence := len(sids_i_j) / len(sids_i)) >= self.min_conf:
            new_rule.confidence = round(rule_confidence, 3)
            self.rules.append(new_rule)

    def find_rule_sequences(self, common_sequences, i, j) -> tuple[set[int], set[int]]:
        sids_i_j = set()
        sids_j_i = set()
        for sequence in common_sequences:
            if self.first_occurrences[i][sequence] < self.last_occurrences[j][sequence]:
                sids_i_j.add(sequence)
            if self.first_occurrences[j][sequence] < self.last_occurrences[i][sequence]:
                sids_j_i.add(sequence)
        return sids_i_j, sids_j_i

    # def remove_items_with_low_support(self) -> None:
    #     to_remove = []
    #     for item in self.sequence_ids:
    #         if len(self.sequence_ids[item])/self.db_size < self.min_sup:
    #             to_remove.append(item)
    #     for item in to_remove:
    #         del self.sequence_ids[item]
    #         del self.first_occurrences[item]
    #         del self.last_occurrences[item]

    def left_search(self, left_equiv):
        pass

    def right_search(self, right_equiv):
        pass

    def print_rules(self) -> None:
        for rule in self.rules:
            print(rule)


if __name__ == "__main__":
    erminer = ERMiner("data/example.txt", 0.5, 0.75)
    erminer.run()
