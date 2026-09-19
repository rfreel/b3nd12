import Base
import ./model.bend as Model
import ./LAWS.bend as Laws

def Laws.accepted_behavior(request):
  match request:
    case Model.Request{False{}, Model.Pass{}, Model.Pass{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Pass{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Pass{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Fail{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Fail{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Fail{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Pending{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Pending{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Pending{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Pass{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Pass{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Pass{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Fail{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Fail{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Fail{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Pending{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Pending{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Pending{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Pass{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Pass{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Pass{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Fail{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Fail{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Fail{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Pending{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Pending{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Pending{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Pass{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Pass{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Pass{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Fail{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Fail{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Fail{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Pending{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Pending{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Pending{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Pass{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Pass{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Pass{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Fail{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Fail{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Fail{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Pending{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Pending{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Pending{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Pass{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Pass{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Pass{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Fail{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Fail{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Fail{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Pending{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Pending{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Pending{}, Model.Pending{}}:
      {==}

def Laws.accepted_preservation(request):
  match request:
    case Model.Request{False{}, Model.Pass{}, Model.Pass{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Pass{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Pass{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Fail{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Fail{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Fail{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Pending{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Pending{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Pending{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Pass{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Pass{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Pass{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Fail{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Fail{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Fail{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Pending{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Pending{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Pending{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Pass{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Pass{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Pass{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Fail{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Fail{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Fail{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Pending{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Pending{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Pending{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Pass{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Pass{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Pass{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Fail{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Fail{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Fail{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Pending{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Pending{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Pending{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Pass{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Pass{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Pass{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Fail{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Fail{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Fail{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Pending{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Pending{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Pending{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Pass{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Pass{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Pass{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Fail{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Fail{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Fail{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Pending{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Pending{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Pending{}, Model.Pending{}}:
      {==}

def Laws.accepted_integrity(request):
  match request:
    case Model.Request{False{}, Model.Pass{}, Model.Pass{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Pass{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Pass{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Fail{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Fail{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Fail{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Pending{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Pending{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Pass{}, Model.Pending{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Pass{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Pass{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Pass{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Fail{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Fail{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Fail{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Pending{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Pending{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Fail{}, Model.Pending{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Pass{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Pass{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Pass{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Fail{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Fail{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Fail{}, Model.Pending{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Pending{}, Model.Pass{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Pending{}, Model.Fail{}}:
      {==}
    case Model.Request{False{}, Model.Pending{}, Model.Pending{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Pass{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Pass{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Pass{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Fail{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Fail{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Fail{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Pending{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Pending{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Pass{}, Model.Pending{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Pass{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Pass{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Pass{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Fail{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Fail{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Fail{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Pending{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Pending{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Fail{}, Model.Pending{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Pass{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Pass{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Pass{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Fail{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Fail{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Fail{}, Model.Pending{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Pending{}, Model.Pass{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Pending{}, Model.Fail{}}:
      {==}
    case Model.Request{True{}, Model.Pending{}, Model.Pending{}, Model.Pending{}}:
      {==}

def Laws.invalid_context_rejected(b, p, i):
  {==}

def Laws.eligible_accepted():
  {==}

def Laws.missing_evidence_waits():
  {==}

def Laws.rejected_preserves_state(before, after):
  {==}

def Laws.pending_preserves_state(before, after):
  {==}

def Laws.accepted_updates_state(before, after):
  {==}
