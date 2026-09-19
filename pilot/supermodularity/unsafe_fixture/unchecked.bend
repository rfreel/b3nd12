# Intentionally unsafe trust-boundary fixture; never import into the pilot.
import Base

@unsafe def identity(value: Bool) -> Bool:
  value
