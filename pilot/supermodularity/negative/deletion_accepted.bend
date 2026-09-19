import Base
import ../model.bend as Model

def false_claim() -> {Model.decide(Model.Proposed{Model.Identity{}, Model.Delete{}}) == Model.Accepted{} : Model.Decision}:
  {==}
