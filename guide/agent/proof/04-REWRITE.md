# 04 Rewrite

Use an equality as a local substitution.

Move
```bend
%eq : {f(_) == target : T}
rest
```

Named equation binder when needed
```bend
%eq@E : P
rest
```

Meaning
The underscore marks the endpoint being replaced in the motive.

Signal
You already have the equality needed to turn the current goal into a convertible one.
