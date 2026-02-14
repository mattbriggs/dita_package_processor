# CLI

The CLI is the **contractual entry point** into the DITA Package Processor. It exposes a small, explicit set of subcommands that correspond directly to pipeline stages: discovery, normalization, planning, execution, and the full `run` pipeline.  

The CLI performs **no domain logic**. Its responsibilities are limited to argument validation, loading and writing artifacts, wiring the correct components together, and reporting failures clearly. It does not inspect XML, interpret plans, or mutate the filesystem implicitly.  

Each command consumes exactly one expected artifact type and produces exactly one output artifact. Invalid combinations fail immediately. This makes the CLI deterministic, scriptable, and safe for automation in batch or CI environments.  

The CLI is intentionally strict. It prioritizes reproducibility and auditability over convenience, and it never guesses user intent.



::: dita_package_processor.cli
    options:
      heading_level: 3
::: dita_package_processor.cli_discover
    options:
      heading_level: 3
::: dita_package_processor.cli_plan
    options:
      heading_level: 3
::: dita_package_processor.cli_run
    options:
      heading_level: 3
::: dita_package_processor.cli_execute
    options:
      heading_level: 3