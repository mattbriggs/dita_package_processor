# Planning

The Planning module converts discovery output into a **deterministic execution plan**. It is where intent is expressed explicitly as ordered actions with clear reasons and traceable origins.  

Planning does not mutate files or execute transformations. It analyzes structure, applies planning steps, and emits a plan that can be reviewed, validated, versioned, and replayed.  

This separation allows complex transformations to be reasoned about and tested independently of execution, and it makes the system explainable by design.

::: dita_package_processor.planning.executor
    options:
      heading_level: 3
::: dita_package_processor.planning.graph_planner
    options:
      heading_level: 3
::: dita_package_processor.planning.hydrator
    options:
      heading_level: 3
::: dita_package_processor.planning.input_normalizer
    options:
      heading_level: 3
::: dita_package_processor.planning.invariants
    options:
      heading_level: 3
::: dita_package_processor.planning.layout_rules
    options:
      heading_level: 3
::: dita_package_processor.planning.loader
    options:
      heading_level: 3
::: dita_package_processor.planning.models
    options:
      heading_level: 3
::: dita_package_processor.planning.planner
    options:
      heading_level: 3
::: dita_package_processor.planning.validation
    options:
      heading_level: 3