import Base
import ./unchecked.bend as Unchecked

def forwarded(value: Bool) -> Bool:
  Unchecked.identity(value)
