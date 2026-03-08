# Execution

The Execution module consumes a validated plan and produces an **ExecutionReport**. It is the only layer allowed to perform filesystem mutation, and only when explicitly enabled.  

Execution resolves paths via a sandbox, enforces mutation policies, dispatches actions to registered handlers, and records outcomes in a structured, forensic report.  

Dry-run execution is fully supported and is the default mode, allowing plans to be validated without side effects. Execution never invents actions or alters plans.

::: dita_package_processor.execution.bootstrap
    options:
      heading_level: 3
::: dita_package_processor.execution.dispatcher
    options:
      heading_level: 3
::: dita_package_processor.execution.dry_run_executor
    options:
      heading_level: 3
::: dita_package_processor.execution.models
    options:
      heading_level: 3
::: dita_package_processor.execution.registry
    options:
      heading_level: 3
::: dita_package_processor.execution.report_writer
    options:
      heading_level: 3