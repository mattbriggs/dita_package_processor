# Steps

The `dita_package_processor.steps` modules are legacy or internal implementation surfaces retained in the repository. They are not the current primary extension mechanism for the tool.

The current public extension model is plugin-based:

- patterns come from plugins
- actions are emitted through plugin planning hooks
- handlers are registered through plugins

These step modules are documented here for completeness and code navigation, but they should not be treated as the preferred external customization API.

::: dita_package_processor.steps.base
    options:
      heading_level: 3
::: dita_package_processor.steps.process_maps
    options:
      heading_level: 3
::: dita_package_processor.steps.refactor_glossary
    options:
      heading_level: 3
::: dita_package_processor.steps.remove_index_map
    options:
      heading_level: 3
::: dita_package_processor.steps.rename_main_map
    options:
      heading_level: 3
