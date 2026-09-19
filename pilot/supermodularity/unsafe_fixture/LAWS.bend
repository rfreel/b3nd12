import Base
import ./bridge.bend as Bridge

law forwarded_true:
  {Bridge.forwarded(True{}) == True{} : Bool}
