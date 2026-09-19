import Base
import ../model.bend as Model

def false_claim() -> {Model.decide(Model.Request{False{}, Model.Pass{}, Model.Pass{}, Model.Pass{}}) == Model.Accepted{} : Model.Decision}:
  {==}
