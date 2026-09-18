# 08 Contradiction and constructor clash

Use an `Empty` inhabitant only when the context already makes the branch impossible.

Direct
A branch with `e : Empty` may eliminate it with the available Empty eliminator.

Constructor clash
For an equality such as `{1n == 0n : Nat}`, define or reuse a discriminator whose result differs by constructor, then rewrite the equality through that discriminator until the impossible branch has type Empty.

Related form
`{a != b : T}` is `{a == b : T} -> Empty`.

Boundary
Do not introduce @unsafe or a nonterminating inhabitant of Empty.
