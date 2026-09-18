# 03 Structural induction

Use when a recursive datatype and recursive definition expose a strictly smaller subterm.

Shape
```bend
def add_zero(x):
  match x:
    case 0n:
      {==}
    case 1n+p:
      %add_zero(p) : {1n+Nat.add(p, 0n) == 1n+_ : Nat}
      {==}
```

Signal
The step case differs from the goal by the same proposition on the recursive field.

Boundary
The recursive proof call must follow Bend's termination rule. Do not use @unsafe to bypass it.
