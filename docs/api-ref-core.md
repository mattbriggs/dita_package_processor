# Core

The Core module defines the **shared abstractions and contracts** used across the entire system. This includes base models, shared utilities, registries, and cross-cutting concerns that must remain stable across pipeline stages.  

Core code is intentionally minimal and conservative. It does not implement discovery, planning, or execution logic directly. Instead, it provides the structural glue that allows those layers to interoperate without tight coupling.  

This layer exists to prevent duplication, enforce consistency, and provide a stable foundation for extension. Changes here have wide impact and are treated as schema-level decisions, not implementation details.


::: dita_package_processor.config
    options:
      heading_level: 3
::: dita_package_processor.dita_xml
    options:
      heading_level: 3
::: dita_package_processor.orchestration
    options:
      heading_level: 3
::: dita_package_processor.pipeline
    options:
      heading_level: 3
::: dita_package_processor.utils
    options:
      heading_level: 3