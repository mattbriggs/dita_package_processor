# Discovery

The Discovery module performs a **read-only structural scan** of a DITA package. Its job is to observe what exists, not to interpret intent or make decisions.  

Discovery identifies artifacts, extracts relationships, and produces a graph-based representation of the package. It does not normalize structure, enforce rules, or infer transformations. All findings are recorded with evidence and confidence where applicable.  

The output of discovery is a durable, schema-validated artifact that represents the structural truth of the package at a point in time. All downstream stages depend on this output and must treat it as authoritative.

::: dita_package_processor.discovery.classifiers
    options:
      heading_level: 3
::: dita_package_processor.discovery.graph
    options:
      heading_level: 3
::: dita_package_processor.discovery.models
    options:
      heading_level: 3
::: dita_package_processor.discovery.path_normalizer
    options:
      heading_level: 3
::: dita_package_processor.discovery.patterns
    options:
      heading_level: 3
::: dita_package_processor.discovery.relationships
    options:
      heading_level: 3
::: dita_package_processor.discovery.report
    options:
      heading_level: 3
::: dita_package_processor.discovery.scanner
    options:
      heading_level: 3
::: dita_package_processor.discovery.signatures
    options:
      heading_level: 3