import Base
import ../model.bend as Model

def false_claim() -> {Model.decide(Model.Request{True{}, Model.Pass{}, Model.Pass{}, Model.Pending{}}) == Model.Accepted{} : Model.Decision}:
  {==}
