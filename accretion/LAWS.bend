# Fixed acceptance law for the three-task routing workload.
# Evidence is emitted by the trusted evaluator, never by the candidate.
import Base
import ./Evidence.bend as E

law improves_next_agent:
  {Bool.and(E.preserved(),
    Bool.and(E.no_regressions(),
      Bool.and(Nat.is_lt(E.after(), E.before()),
        Nat.is_le(E.candidate_bytes(), 4096n)))) == True{} : Bool}
