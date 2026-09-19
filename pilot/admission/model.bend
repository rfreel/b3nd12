# The finite decision kernel abstracts authenticated facts, not their acquisition.
import Base

type Status is Data:
  Pass{}
  Fail{}
  Pending{}

type Decision is Data:
  Accepted{}
  Rejected{}
  Waiting{}

type Request is Data:
  Request{context: Bool, behavior: Status, preservation: Status, integrity: Status}

def combine(left: Status, right: Status) -> Status:
  match left:
    case Fail{}:
      Fail{}
    case Pass{}:
      right
    case Pending{}:
      match right:
        case Fail{}:
          Fail{}
        case Pass{}:
          Pending{}
        case Pending{}:
          Pending{}

def verdict(status: Status) -> Decision:
  match status:
    case Pass{}:
      Accepted{}
    case Fail{}:
      Rejected{}
    case Pending{}:
      Waiting{}

def decide(request: Request) -> Decision:
  match request:
    case Request{False{}, b, p, i}:
      Rejected{}
    case Request{True{}, b, p, i}:
      verdict(combine(b, combine(p, i)))

def implies_pass(decision: Decision, status: Status) -> Bool:
  match decision:
    case Rejected{}:
      True{}
    case Waiting{}:
      True{}
    case Accepted{}:
      match status:
        case Pass{}:
          True{}
        case Fail{}:
          False{}
        case Pending{}:
          False{}

def behavior_holds(request: Request) -> Bool:
  match request:
    case Request{+c, +b, +p, +i}:
      implies_pass(decide(Request{c, b, p, i}), b)

def preservation_holds(request: Request) -> Bool:
  match request:
    case Request{+c, +b, +p, +i}:
      implies_pass(decide(Request{c, b, p, i}), p)

def integrity_holds(request: Request) -> Bool:
  match request:
    case Request{+c, +b, +p, +i}:
      implies_pass(decide(Request{c, b, p, i}), i)

def update(decision: Decision, before: Bool, after: Bool) -> Bool:
  match decision:
    case Accepted{}:
      after
    case Rejected{}:
      before
    case Waiting{}:
      before
