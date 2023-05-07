
def read_database(path: str) -> list[list[set[int]]]:
    sequences = []
    with open(path) as file:
        for line in file:
            if line[0] != '-':
                sequences.append([set(map(int, transaction.split()))
                                  for transaction in line.rstrip("-1 -2\n").split("-1")])
    return sequences


def ERMiner(sequences, minsup, mincon):
    pass


def left_search(left_equiv, rules, minsup, mincon):
    pass


def right_search(right_equiv, rules, minsup, mincon):
    pass


if __name__ == "__main__":
    print(read_database("data/example.txt"))
