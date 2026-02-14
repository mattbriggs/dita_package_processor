# Knowledge

The Knowledge module provides **pattern definitions and classification logic** used during discovery and planning. It encodes reusable heuristics about DITA structures, naming conventions, and common package layouts.  

This layer is descriptive, not prescriptive. It does not execute transformations or mutate data. Instead, it supplies structured knowledge that other stages can reference when making decisions.  

By isolating heuristics in this module, the system avoids hard-coding assumptions into discovery or planning logic and makes those assumptions explicit, testable, and replaceable.

::: dita_package_processor.knowledge.invariants
    options:
      heading_level: 3
::: dita_package_processor.knowledge.known_patterns
    options:
      heading_level: 3
::: dita_package_processor.knowledge.map_types
    options:
      heading_level: 3