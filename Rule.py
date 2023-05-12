class Rule:
    def __init__(self, antecedent: set[int], consequent: set[int],
                 support: float = 0., confidence: float = 0.):
        self.antecedent: set[int] = antecedent
        self.consequent: set[int] = consequent
        self.support: float = support
        self.confidence: float = confidence

    def __str__(self) -> str:
        return f"{self.antecedent} => {self.consequent}, support={self.support}, confidence={self.confidence}"
