import Base
import ./model.bend as Model

# A: required behavior.
law accepted_behavior:
  for request: Model.Request
  {Model.behavior_holds(request) == True{} : Bool}

# B: preserved obligations.
law accepted_preservation:
  for request: Model.Request
  {Model.preservation_holds(request) == True{} : Bool}

# C: evaluation integrity.
law accepted_integrity:
  for request: Model.Request
  {Model.integrity_holds(request) == True{} : Bool}

law invalid_context_rejected:
  for b: Model.Status
  for p: Model.Status
  for i: Model.Status
  {Model.decide(Model.Request{False{}, b, p, i}) == Model.Rejected{} : Model.Decision}

law eligible_accepted:
  {Model.decide(Model.Request{True{}, Model.Pass{}, Model.Pass{}, Model.Pass{}}) == Model.Accepted{} : Model.Decision}

law missing_evidence_waits:
  {Model.decide(Model.Request{True{}, Model.Pass{}, Model.Pass{}, Model.Pending{}}) == Model.Waiting{} : Model.Decision}

law rejected_preserves_state:
  for before: Bool
  for after: Bool
  {Model.update(Model.Rejected{}, before, after) == before : Bool}

law pending_preserves_state:
  for before: Bool
  for after: Bool
  {Model.update(Model.Waiting{}, before, after) == before : Bool}

law accepted_updates_state:
  for before: Bool
  for after: Bool
  {Model.update(Model.Accepted{}, before, after) == after : Bool}
