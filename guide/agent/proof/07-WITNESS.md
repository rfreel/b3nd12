# 07 Witness construction

Use when a law contains `exs`.

Law shape
```bend
law example:
  exs y: Nat
  {P(y)}
```

Proof result
```bend
(y, proof)
```

Nested existentials return nested dependent pairs in declaration order.

Signal
The goal asks for data plus evidence. Construct the witness before proving its property when the witness is determined by the computation.
