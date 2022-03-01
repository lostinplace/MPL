class MPLEngine:
    def __init__(self, mpl_interpreter):
        self.mpl_interpreter = mpl_interpreter
        self.mpl_interpreter.mpl_engine = self

    def evaluate_rule(self, rule):
        return self.mpl_interpreter.evaluate_rule(rule)