# Finite repair pilot. The specification is Boolean identity.
# Baseline fails True; ConstantTrue fixes it but breaks False.
import Base

type Program is Data:
  ConstantFalse{}
  Identity{}
  ConstantTrue{}

type EvidenceEdit is Data:
  Retain{}
  Delete{}

type Candidate is Data:
  Proposed{program: Program, evidence: EvidenceEdit}
  Unresolved{}

type Decision is Data:
  Accepted{}
  Rejected{}
  Pending{}

# These are actual stored input/output cases, not an evidence checksum.
type Case is Data:
  Case{input: Bool, expected: Bool}

def recorded() -> List<Case>:
  [Case{False{}, False{}}, Case{True{}, True{}}]

def evidence(edit: EvidenceEdit) -> List<Case>:
  match edit:
    case Retain{}:
      recorded()
    case Delete{}:
      []

def run(program: Program, input: Bool) -> Bool:
  match program:
    case ConstantFalse{}:
      False{}
    case Identity{}:
      input
    case ConstantTrue{}:
      True{}

def target_passes(program: Program) -> Bool:
  run(program, True{})

def regression_passes(program: Program) -> Bool:
  Bool.not(run(program, False{}))

def decide_checked(passes: Bool) -> Decision:
  match passes:
    case True{}:
      Accepted{}
    case False{}:
      Rejected{}

def decide(candidate: Candidate) -> Decision:
  match candidate:
    case Unresolved{}:
      Pending{}
    case Proposed{+program, +edit}:
      match edit:
        case Delete{}:
          Rejected{}
        case Retain{}:
          decide_checked(Bool.and(target_passes(program), regression_passes(program)))

def evidence_checked(decision: Decision, edit: EvidenceEdit) -> List<Case>:
  match decision:
    case Accepted{}:
      evidence(edit)
    case Rejected{}:
      recorded()
    case Pending{}:
      recorded()

def output_checked(decision: Decision, passes: Bool) -> Bool:
  match decision:
    case Accepted{}:
      passes
    case Rejected{}:
      True{}
    case Pending{}:
      True{}

# Rejected or unresolved candidates leave the existing ledger intact.
def committed_evidence(candidate: Candidate) -> List<Case>:
  match candidate:
    case Unresolved{}:
      recorded()
    case Proposed{+program, +edit}:
      evidence_checked(decide(Proposed{program, edit}), edit)

# Explicit implication, so these functions do not imply all candidates pass.
def accepted_target(candidate: Candidate) -> Bool:
  match candidate:
    case Unresolved{}:
      True{}
    case Proposed{+program, +edit}:
      output_checked(decide(Proposed{program, edit}), target_passes(program))

def accepted_regression(candidate: Candidate) -> Bool:
  match candidate:
    case Unresolved{}:
      True{}
    case Proposed{+program, +edit}:
      output_checked(decide(Proposed{program, edit}), regression_passes(program))
