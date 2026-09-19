# Finite-model guarantees only. External measurements are separate evidence.
import Base
import ./model.bend as Model

law evidence_retained:
  for candidate: Model.Candidate
  {Model.committed_evidence(candidate) == Model.recorded() : List<Model.Case>}

law accepted_repairs_target:
  for candidate: Model.Candidate
  {Model.accepted_target(candidate) == True{} : Bool}

law accepted_preserves_regression:
  for candidate: Model.Candidate
  {Model.accepted_regression(candidate) == True{} : Bool}

law valid_repair_accepted:
  {Model.decide(Model.Proposed{Model.Identity{}, Model.Retain{}}) == Model.Accepted{} : Model.Decision}

law broken_repair_rejected:
  {Model.decide(Model.Proposed{Model.ConstantFalse{}, Model.Retain{}}) == Model.Rejected{} : Model.Decision}

law regression_break_rejected:
  {Model.decide(Model.Proposed{Model.ConstantTrue{}, Model.Retain{}}) == Model.Rejected{} : Model.Decision}

law evidence_deletion_rejected:
  {Model.decide(Model.Proposed{Model.Identity{}, Model.Delete{}}) == Model.Rejected{} : Model.Decision}

law unresolved_preserved:
  {Model.decide(Model.Unresolved{}) == Model.Pending{} : Model.Decision}
