# CLI API Reference

The CLI is the process entry point and routing layer. It registers the current command surface, global options, and command dispatch. Domain logic lives below the CLI.

Current command groups:

- discovery and planning transport commands
- execution and full-pipeline orchestration commands
- plugin inspection and validation commands
- auxiliary `docs` and `completion` commands

::: dita_package_processor.cli
    options:
      heading_level: 3
::: dita_package_processor.cli_discover
    options:
      heading_level: 3
::: dita_package_processor.cli_normalize
    options:
      heading_level: 3
::: dita_package_processor.cli_plan
    options:
      heading_level: 3
::: dita_package_processor.cli_execute
    options:
      heading_level: 3
::: dita_package_processor.cli_run
    options:
      heading_level: 3
::: dita_package_processor.cli_plugin
    options:
      heading_level: 3
