import Base
import ./model.bend as Model
import ./LAWS.bend as Laws

def Laws.evidence_retained(candidate):
  match candidate:
    case Model.Unresolved{}:
      {==}
    case Model.Proposed{Model.ConstantFalse{}, Model.Retain{}}:
      {==}
    case Model.Proposed{Model.ConstantFalse{}, Model.Delete{}}:
      {==}
    case Model.Proposed{Model.Identity{}, Model.Retain{}}:
      {==}
    case Model.Proposed{Model.Identity{}, Model.Delete{}}:
      {==}
    case Model.Proposed{Model.ConstantTrue{}, Model.Retain{}}:
      {==}
    case Model.Proposed{Model.ConstantTrue{}, Model.Delete{}}:
      {==}

def Laws.accepted_repairs_target(candidate):
  match candidate:
    case Model.Unresolved{}:
      {==}
    case Model.Proposed{Model.ConstantFalse{}, Model.Retain{}}:
      {==}
    case Model.Proposed{Model.ConstantFalse{}, Model.Delete{}}:
      {==}
    case Model.Proposed{Model.Identity{}, Model.Retain{}}:
      {==}
    case Model.Proposed{Model.Identity{}, Model.Delete{}}:
      {==}
    case Model.Proposed{Model.ConstantTrue{}, Model.Retain{}}:
      {==}
    case Model.Proposed{Model.ConstantTrue{}, Model.Delete{}}:
      {==}

def Laws.accepted_preserves_regression(candidate):
  match candidate:
    case Model.Unresolved{}:
      {==}
    case Model.Proposed{Model.ConstantFalse{}, Model.Retain{}}:
      {==}
    case Model.Proposed{Model.ConstantFalse{}, Model.Delete{}}:
      {==}
    case Model.Proposed{Model.Identity{}, Model.Retain{}}:
      {==}
    case Model.Proposed{Model.Identity{}, Model.Delete{}}:
      {==}
    case Model.Proposed{Model.ConstantTrue{}, Model.Retain{}}:
      {==}
    case Model.Proposed{Model.ConstantTrue{}, Model.Delete{}}:
      {==}

def Laws.valid_repair_accepted():
  {==}

def Laws.broken_repair_rejected():
  {==}

def Laws.regression_break_rejected():
  {==}

def Laws.evidence_deletion_rejected():
  {==}

def Laws.unresolved_preserved():
  {==}
