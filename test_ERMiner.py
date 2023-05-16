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
        assert len(erminer.sequence_ids[1]) == 5
        assert len(erminer.sequence_ids[2]) == 4
