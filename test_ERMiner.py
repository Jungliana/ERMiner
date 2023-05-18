from ERMiner import ERMiner


class TestERMiner:

    def test_line_read(self):
        line = '3 1 -1 2 -1 -2\n'
        sequence = [set(map(int, transaction.split()))
                    for transaction in line[:-7].split('-1')]
        assert sequence == [{3, 1}, {2}]

    def test_read_database(self):
        erminer = ERMiner("data/test_example.txt", 0., 0.)
        erminer.read_database("data/test_example.txt")
        assert len(erminer.sequence_ids[1]) == 5  # item 1 is in 5 sequences
        assert len(erminer.sequence_ids[2]) == 4  # item 2 is in 4 sequences
        assert 4 not in erminer.sequence_ids[2]  # item 2 is not in the last sequence

    def test_first_last_occurrences(self):
        erminer = ERMiner("data/test_example.txt", 0., 0.)
        erminer.read_database("data/test_example.txt")
        assert erminer.first_occurrences[1][0] == 0
        assert erminer.first_occurrences[1][1] == 1
        assert erminer.first_occurrences[1][2] == 0
        assert erminer.last_occurrences[1][2] == 0
        assert erminer.first_occurrences[1][4] != erminer.last_occurrences[1][4]
        assert erminer.first_occurrences[1][2] == erminer.first_occurrences[2][2]
        assert erminer.last_occurrences[1][2] == erminer.last_occurrences[2][2]

    def test_removed_items(self):
        erminer = ERMiner("data/test_example.txt", 0.5, 0.)
        erminer.read_database("data/test_example.txt")
        assert 3 not in erminer.sequence_ids.keys()

        erminer = ERMiner("data/test_example.txt", 0., 0.)
        erminer.read_database("data/test_example.txt")
        assert 3 in erminer.sequence_ids.keys()
        assert erminer.first_occurrences[3][4] == 2

    def test_find_all_rules(self):
        erminer = ERMiner("data/test_example.txt", 0.01, 0.01)
        erminer.run(printing=False)
        # Should find all 3 rules: 1 -> 2, 2 -> 1, 1 -> 3
        assert len(erminer.rules) == 3

    def test_find_frequent_rules(self):
        erminer = ERMiner("data/test_example.txt", 0.4, 0.3)
        erminer.run(printing=False)
        # Should find 2 rules: 1 -> 2, 2 -> 1
        assert len(erminer.rules) == 2
