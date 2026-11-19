# -*- coding: utf-8 -*-

class ExpressionEvaluator:
    PRECEDENCE = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
    RIGHT_ASSOC = {'^'}

    def _tokenize(self, expr: str) -> list[str]:
        tokens = []
        i = 0
        while i < len(expr):
            char = expr[i]
            if char.isspace():
                i += 1
                continue
            elif char in ('+', '*', '/', '^', '(', ')'):
                tokens.append(char)
                i += 1
            elif char == '-':
                # Unaier si au debut ou apres operateur ou parenthèse ouvrante
                if not tokens or tokens[-1] in ('+', '-', '*', '/', '^', '('):
                    # Cherche le nombre qui suit
                    start = i + 1
                    while start < len(expr) and expr[start].isspace():
                        start += 1
                    if start < len(expr) and (expr[start].isdigit() or expr[start] == '.'):
                        end = start
                        while end < len(expr) and (expr[end].isdigit() or expr[end] == '.'):
                            end += 1
                        tokens.append('-' + expr[start:end])
                        i = end
                    elif start < len(expr) and expr[start] == '(':
                        tokens.append('-1')
                        tokens.append('*')
                        i = start
                    else:
                        raise ValueError(f'Invalid token after unary minus: {char}')
                else:
                    tokens.append('-')
                    i += 1
            elif char.isdigit() or char == '.':
                start = i
                while i < len(expr) and (expr[i].isdigit() or expr[i] == '.'):
                    i += 1
                tokens.append(expr[start:i])
            else:
                raise ValueError(f'Invalid character: {char}')
        return tokens

    def apply_op(self, values, ops):
        if not ops or len(values) < 2:
            raise ValueError('Invalid expression structure')
        op = ops.pop()
        b = values.pop()
        a = values.pop()
        if op == '+': values.append(a + b)
        elif op == '-': values.append(a - b)
        elif op == '*': values.append(a * b)
        elif op == '/':
            if b == 0: raise ZeroDivisionError('Division par zéro')
            values.append(a / b)
        elif op == '^': values.append(a ** b)

    def evaluate(self, expr: str) -> float:
        tokens = self._tokenize(expr)
        if not tokens:
            raise ValueError('Empty expression')

        values = []
        ops = []

        for token in tokens:
            if token.replace('.', '', 1).isdigit() or (token.startswith('-') and token[1:].replace('.', '', 1).isdigit()):
                values.append(float(token))
            elif token == '(':
                ops.append(token)
            elif token == ')':
                while ops and ops[-1] != '(':
                    self.apply_op(values, ops)
                if not ops or ops[-1] != '(':
                    raise ValueError('Unmatched parentheses')
                ops.pop()
            elif token in self.PRECEDENCE:
                op1 = token
                while (ops and ops[-1] != '(' and 
                       (self.PRECEDENCE.get(ops[-1], 0) > self.PRECEDENCE[op1] or 
                       (self.PRECEDENCE.get(ops[-1], 0) == self.PRECEDENCE[op1] and op1 not in self.RIGHT_ASSOC))):
                    self.apply_op(values, ops)
                ops.append(op1)
            else:
                raise ValueError(f'Unknown token: {token}')

        while ops:
            if ops[-1] == '(':
                raise ValueError('Unmatched parentheses')
            self.apply_op(values, ops)

        if len(values) != 1:
            raise ValueError('Invalid expression evaluation')

        return values[0]
