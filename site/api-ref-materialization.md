# Materialization

Materialization is responsible for **turning execution intent into concrete outputs**. It bridges the gap between abstract actions and tangible artifacts, such as files, directories, or reports.  

This module does not decide *what* should happen. It only concerns itself with *how* declared actions are realized in a controlled environment. Safety guarantees, sandboxing, and idempotence are central concerns.  

Materialization logic is designed to be deterministic and auditable, ensuring that the same plan always produces the same results under the same conditions.

::: dita_package_processor.materialization.builder
    options:
      heading_level: 3
::: dita_package_processor.materialization.collision
    options:
      heading_level: 3
::: dita_package_processor.materialization.layout
    options:
      heading_level: 3
::: dita_package_processor.materialization.models
    options:
      heading_level: 3
::: dita_package_processor.materialization.orchestrator
    options:
      heading_level: 3
::: dita_package_processor.materialization.validation
    options:
      heading_level: 3