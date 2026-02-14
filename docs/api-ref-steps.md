# Steps

The Steps module contains **modular planning steps** that encapsulate specific transformation logic. Each step inspects discovery or normalized data and emits plan actions when its conditions are met.  

Steps do not execute transformations. They do not access the filesystem. Their sole responsibility is to recognize patterns and express intent declaratively.  

This design allows new behaviors to be added by introducing new steps, without modifying the planner core or execution layer. Steps are where domain knowledge becomes explicit, reviewable, and extensible.

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