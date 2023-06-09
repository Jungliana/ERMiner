from collections import defaultdict
from math import ceil
import datetime


class Rule:
    def __init__(self, antecedent: set[int], consequent: set[int], support: float = 0.,
                 confidence: float = 0., sequences=None, antecedent_sequences=None) -> None:
        self.antecedent: set[int] = antecedent
        self.consequent: set[int] = consequent
        self.support: float = support
        self.confidence: float = confidence
        self.sequences: set[int] = {} if sequences is None else sequences
        self.antecedent_sequences: set[int] = {} if antecedent_sequences is None else antecedent_sequences

    def __str__(self) -> str:
        return f"{self.antecedent} => {self.consequent}, support={self.support}, confidence={self.confidence}"


class ERMiner:
    ROUND_DIGITS = 3
    ERROR_RETURN = -1

    def __init__(self, path: str, min_sup: float = 0.5, min_con: float = 0.75, output: str = "output.txt"):
        self.database_file: str = path
        self.output: str = output
        self.db_size: int = 0
        self.min_sup: float = min_sup
        self.min_conf: float = min_con
        self.min_rules_sup: int = 0

        self.left_equivalence = defaultdict(list)
        self.right_equivalence = defaultdict(list)
        self.left_store = defaultdict(lambda: defaultdict(list))
        self.rules: list[Rule] = []

        # for every item, set of sequence ids where it occurs, eg. {1:{1, 2, 3}, 2:{1, 3, 4}...}
        self.sequence_ids = defaultdict(set)
        # for every item, dict seq id:first(last) occurrence, eg. {1:{1:1, 2:4, 3:2}, 2:{1:2}...}
        self.first_occurrences = defaultdict(dict)
        self.last_occurrences = defaultdict(dict)

    def run(self, printing: bool = True, out_file: bool = False) -> tuple[float, int]:
        """
        Run the ERMiner algorithm: scan the database once,
        find all valid rules, then print them.
        """
        start = datetime.datetime.now()
        try:
            self.read_database(self.database_file)
        except Exception as e:
            print(f"Problem with file: {e}.")
            return self.ERROR_RETURN, self.ERROR_RETURN
        self.find_rules()
        end = datetime.datetime.now()
        if out_file:
            self.write_output()
        if printing:
            self.print_rules()
        print(f'\nTime: {(end - start).total_seconds()} [s], rules found: {len(self.rules)}')
        return (end - start).total_seconds(), len(self.rules)

    def read_database(self, path: str, separator: str = "-1") -> None:
        """
        Read a sequence database from a text file.
        """
        with open(path) as file:
            for i, line in enumerate(file):
                if line[0] not in '-\n':  # Don't scan empty sequences
                    self.db_size += 1
                    sequence = [set(map(int, transaction.split()))
                                for transaction in line[:-6].split(separator)]
                    self.scan_sequence(sequence, i)
        self.min_rules_sup = ceil(self.min_sup * self.db_size)
        self.remove_items_with_low_support()

    def scan_sequence(self, sequence: list[set[int]], sequence_id: int) -> None:
        """
        Scan a sequence to record every item's first and last occurrence.
        Add this sequence id to the set of sequences where the item appears.
        """
        for j, itemset in enumerate(sequence):
            for item in itemset:
                self.sequence_ids[item].add(sequence_id)
                self.last_occurrences[item].update({sequence_id: j})
                if sequence_id not in self.first_occurrences[item].keys():
                    self.first_occurrences[item].update({sequence_id: j})

    def remove_items_with_low_support(self) -> None:
        """
        Remove items with support lower than min_sup.
        """
        for item in list(self.sequence_ids.keys()):
            if len(self.sequence_ids[item]) < self.min_rules_sup:
                del self.sequence_ids[item]
                del self.first_occurrences[item]
                del self.last_occurrences[item]

    def find_rules(self) -> None:
        """
        Find all valid sequential rules in the sequence database.
        """
        all_item_ids = list(self.sequence_ids)
        for last_i, i in enumerate(all_item_ids):
            for j in all_item_ids[last_i+1:]:
                common_sequences = self.sequence_ids[i] & self.sequence_ids[j]
                if len(common_sequences) >= self.min_rules_sup:
                    sids_i_j, sids_j_i = self.find_rule_sequences(common_sequences, i, j)
                    self.build_equivalences(i, j, sids_i_j)
                    self.build_equivalences(j, i, sids_j_i)
        self.do_searches()

    def build_equivalences(self, antecedent: int, consequent: int, sids: set[int]) -> None:
        """
        Build equivalence classes of rules of size 1*1.
        """
        if (rule_support := len(sids)) >= self.min_rules_sup:
            new_rule = Rule({antecedent}, {consequent}, rule_support, sequences=sids,
                            antecedent_sequences=self.sequence_ids[antecedent])
            self.left_equivalence[antecedent].append(new_rule)
            self.right_equivalence[consequent].append(new_rule)
            self.check_rule_confidence(new_rule, self.sequence_ids[antecedent], sids)

    def check_rule_confidence(self, new_rule: Rule, sids_i: set[int], sids_i_j: set[int]) -> None:
        """
        Check the confidence of the rule. If rule confidence >= min confidence
        then add the rule to the list of discovered rules.
        """
        if (rule_confidence := len(sids_i_j) / len(sids_i)) >= self.min_conf:
            new_rule.confidence = round(rule_confidence, ERMiner.ROUND_DIGITS)
            self.rules.append(new_rule)

    def find_rule_sequences(self, common_sequences: set[int], i: int, j: int) -> tuple[set[int], set[int]]:
        """
        Find all sequences supporting a rule where item `i` is in the antecedent, `j` is in the consequent
        and a rule where item `j` is in the antecedent, `i` is in the consequent.
        """
        sids_i_j = set()
        sids_j_i = set()
        for sequence in common_sequences:
            if self.first_occurrences[i][sequence] < self.last_occurrences[j][sequence]:
                sids_i_j.add(sequence)
            if self.first_occurrences[j][sequence] < self.last_occurrences[i][sequence]:
                sids_j_i.add(sequence)
        return sids_i_j, sids_j_i

    def do_searches(self) -> None:
        """
        Call left_search on all left equivalence classes,
        then call right_search on all right equivalence classes,
        then call left_search again on the left equivalence classes from left store.
        """
        for left_class in self.left_equivalence:
            self.left_search(self.left_equivalence[left_class])
        for right_class in self.right_equivalence:
            self.right_search(self.right_equivalence[right_class])
        for left_class_size in self.left_store:
            for itemset in self.left_store[left_class_size]:
                self.left_search(self.left_store[left_class_size][itemset])

    def left_search(self, left_equiv: list[Rule]) -> None:
        """
        Do the left search on the left equivalence class of rules.
        """
        for i in range(len(left_equiv)):
            left_equiv_prim = []
            for j in range(i+1, len(left_equiv)):
                self.left_merge(left_equiv[i], left_equiv[j], left_equiv_prim)
            self.left_search(left_equiv_prim)

    def left_merge(self, rule_s: Rule, rule_r: Rule, left_equiv: list[Rule]) -> None:
        """
        Perform a left merge on two rules from the same left equivalence class.
        """
        rule_sequences = rule_s.sequences & rule_r.sequences
        if (rule_support := len(rule_sequences)) >= self.min_rules_sup:
            new_rule = Rule(rule_s.antecedent, rule_s.consequent | rule_r.consequent, rule_support,
                            sequences=rule_sequences, antecedent_sequences=rule_s.antecedent_sequences)

            if (rule_confidence := len(rule_sequences) / len(rule_s.antecedent_sequences)) >= self.min_conf:
                new_rule.confidence = rule_confidence
                self.rules.append(new_rule)
            left_equiv.append(new_rule)

    def right_search(self, right_equiv: list[Rule]) -> None:
        """
        Do the right search on the right equivalence class of rules.
        """
        for i in range(len(right_equiv)):
            right_equiv_prim = []
            for j in range(i+1, len(right_equiv)):
                self.right_merge(right_equiv[i], right_equiv[j], right_equiv_prim)
            self.right_search(right_equiv_prim)

    def right_merge(self, rule_s: Rule, rule_r: Rule, right_equiv: list[Rule]) -> None:
        """
        Perform a right merge on two rules from the same right equivalence class.
        """
        rule_sequences = rule_s.sequences & rule_r.sequences
        if (rule_support := len(rule_sequences)) >= self.min_rules_sup:
            antecedent_sequences = rule_s.antecedent_sequences & rule_r.antecedent_sequences
            new_rule = Rule(rule_s.antecedent | rule_r.antecedent, rule_s.consequent, rule_support,
                            sequences=rule_sequences, antecedent_sequences=antecedent_sequences)

            if (rule_confidence := len(rule_sequences) / len(antecedent_sequences)) >= self.min_conf:
                new_rule.confidence = rule_confidence
                self.rules.append(new_rule)
            right_equiv.append(new_rule)
            self.left_store[len(new_rule.antecedent)][frozenset(new_rule.antecedent)].append(new_rule)

    def print_rules(self) -> None:
        """
        Print all valid sequential rules found in the database.
        """
        for rule in self.rules:
            print(rule)

    def write_output(self) -> None:
        """
        Output to a file all valid sequential rules found in the database.
        """
        try:
            with open(self.output, 'w') as fp:
                for rule in self.rules:
                    fp.write("%s\n" % rule)
        except Exception as e:
            print(f"Problem with output: {e}.")
