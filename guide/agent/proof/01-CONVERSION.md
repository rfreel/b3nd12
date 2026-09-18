# 01 Conversion

Use when both sides of the goal compute to the same term.

Move
```bend
{==}
```

Signal
The goal is an equality and no semantic bridge is needed after normalization.

Example
```bend
def zero_case():
  {==}
```

Stop
If conversion does not close the goal, do not add noise. Inspect the residual and choose another move.
