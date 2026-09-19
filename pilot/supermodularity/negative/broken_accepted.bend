import Base
import ../model.bend as Model

def false_claim() -> {Model.decide(Model.Proposed{Model.ConstantFalse{}, Model.Retain{}}) == Model.Accepted{} : Model.Decision}:
  {==}
