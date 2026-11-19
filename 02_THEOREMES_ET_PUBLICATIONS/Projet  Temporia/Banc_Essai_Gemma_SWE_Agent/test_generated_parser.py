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
            
            # Gestion des nombres (incluant les nombres négatifs)
            if char.isdigit() or char == '.':
                start = i
                while i < len(expr) and (expr[i].isdigit() or expr[i] == '.'):
                    i += 1
                num_str = expr[start:i]
                if num_str.startswith('-') and num_str[1:].isdigit() or (num_str.startswith('-') and num_str[1] == '.'):
                    # Si le signe est au début ou suivi d'un point, on le traite comme un nombre négatif
                    tokens.append(num_str)
                else:
                    tokens.append(num_str)
            
            # Opérateurs et parenthèses
            elif char in '+-*/^()':
                tokens.append(char)
                i += 1
            else:
                raise ValueError(f"Caractère invalide trouvé : {char} dans l'expression.")
        return tokens

    def evaluate(self, expr: str) -> float:
        tokens = self._tokenize(expr)
        values = []
        ops = []

        def apply_op():
            if not ops:
                raise ValueError("Opérateur non défini ou expression mal formée.")
            op = ops.pop()
            b = values.pop()
            a = values.pop()

            if op == '+':
                result = a + b
            elif op == '-':
                result = a - b
            elif op == '*':
                result = a * b
            elif op == '/':
                if b == 0:
                    raise ZeroDivisionError("Division par zéro.")
                result = a / b
            elif op == '^':
                result = a ** b
            else:
                raise ValueError(f"Opérateur inconnu : {op}")
            values.append(result)

        for token in tokens:
            if token.replace('.', '', 1).isdigit() or (token.startswith('-') and token[1:].replace('.', '', 1).isdigit()):
                # C'est un nombre
                values.append(float(token))
            elif token == '(':
                ops.append(token)
            elif token == ')':
                # Fermeture des parenthèses
                while ops and ops[-1] != '(':
                    apply_op()
                if not ops or ops[-1] != '(': 
                    raise ValueError("Erreur de parenthèse : Parenthèse fermante sans parenthèse ouvrante correspondante.")
                ops.pop() # Supprime '('
            elif token in PRECEDENCE:
                # C'est un opérateur
                op1 = token
                while (ops and ops[-1] != '(' and 
                       (PRECEDENCE.get(ops[-1], 0) > PRECEDENCE[op1]) or 
                       (PRECEDENCE.get(ops[-1], 0) == PRECEDENCE[op1] and op1 not in RIGHT_ASSOC))
                {
                    apply_op()
                }
                ops.append(op1)
            else:
                raise ValueError(f"Opérateur ou symbole inconnu : {token}")

        # Après la lecture de tous les tokens, appliquer les opérations restantes
        while ops:
            if ops[-1] == '(': 
                raise ValueError("Erreur de parenthèse : Parenthèse ouvrante non fermée.")
            apply_op()

        if len(values) != 1:
            raise ValueError("Expression mal formée : Nombre d'opérations non résolues ou nombre de valeurs incorrect.")

        return values[0]