# 06 Equality direction and chain

Reverse
```bend
Equal.sym(T, a, b, eq)
```

Chain
```bend
Equal.trans(T, a, b, c, ab, bc)
```

Signal
The right fact exists but points the wrong way, or the target requires an intermediate term.

Rule
Choose the smallest intermediate term that makes both legs directly supported. Do not manufacture a long chain when one rewrite closes the goal.
