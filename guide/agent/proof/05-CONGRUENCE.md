# 05 Congruence

Use when an equality must be transported through a function.

Move
```bend
Equal.cong(A, B, f, a, b, eq)
```

Shape
Given `eq : {a == b : A}`, obtain `{f(a) == f(b) : B}`.

Signal
The mismatch is outside an already proved equality, such as a constructor, projection, arithmetic wrapper, or normalization function.

Prefer this to manually rewriting several surrounding layers.
