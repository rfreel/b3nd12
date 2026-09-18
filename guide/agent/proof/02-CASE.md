# 02 Case analysis

Use when the goal depends on which constructor a value has.

Move
```bend
match x:
  case Zero{}:
    ...
  case Succ{p}:
    ...
```

For Nat syntax, constructor patterns may print as `0n` and `1n+p`.

Signal
A datatype value blocks reduction or different constructors require different evidence.

Stop
Keep branches separate when their residual goals differ.
