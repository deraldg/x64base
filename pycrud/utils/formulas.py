import ast, operator as op, math, datetime

# Safe eval for simple expressions (numbers, strings, + - * / // % **, comparisons, and a few funcs)
ALLOWED_FUNCS = {
    "abs": abs, "round": round, "len": len, "min": min, "max": max,
    "sqrt": math.sqrt, "floor": math.floor, "ceil": math.ceil,
    "upper": lambda s: str(s).upper(), "lower": lambda s: str(s).lower(),
    "substr": lambda s, i, n=None: str(s)[i:(None if n is None else i+n)],
    "today": lambda: datetime.date.today().isoformat().replace("-", ""),
}

ALLOWED_OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv, ast.Mod: op.mod, ast.Pow: op.pow,
    ast.Eq: op.eq, ast.NotEq: op.ne, ast.Gt: op.gt, ast.GtE: op.ge, ast.Lt: op.lt, ast.LtE: op.le,
    ast.And: lambda a,b: a and b, ast.Or: lambda a,b: a or b
}

def _eval(node, names):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return names.get(node.id)
    if isinstance(node, ast.BinOp):
        return ALLOWED_OPS[type(node.op)](_eval(node.left, names), _eval(node.right, names))
    if isinstance(node, ast.BoolOp):
        val = _eval(node.values[0], names)
        for v in node.values[1:]:
            val = ALLOWED_OPS[type(node.op)](val, _eval(v, names))
        return val
    if isinstance(node, ast.Compare):
        left = _eval(node.left, names)
        for opnode, comparator in zip(node.ops, node.comparators):
            right = _eval(comparator, names)
            if not ALLOWED_OPS[type(opnode)](left, right):
                return False
            left = right
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        val = _eval(node.operand, names)
        return +val if isinstance(node.op, ast.UAdd) else -val
    if isinstance(node, ast.Call):
        func = node.func.id if isinstance(node.func, ast.Name) else None
        if func not in ALLOWED_FUNCS:
            raise ValueError("Function not allowed")
        args = [_eval(a, names) for a in node.args]
        return ALLOWED_FUNCS[func](*args)
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")

def eval_expr(expr: str, names: dict):
    node = ast.parse(expr, mode="eval").body
    return _eval(node, names)
