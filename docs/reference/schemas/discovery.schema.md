# DITA Package Discovery Contract

Stable discovery contract describing the observable structure of a DITA package. Artifacts represent files, the graph represents structural truth, and relationships are a backward-compatible projection of graph edges.

## Properties

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `artifacts` | array | yes | Complete inventory of discovered package artifacts, including maps, topics, and media files. |
| `relationships` | array | yes | Backward-compatible flat list of structural relationships. This is an alias of graph.edges and exists to support legacy consumers. |
| `graph` | object | yes | Canonical structural graph of the package. Nodes represent semantic artifacts, and edges represent directed relationships between them. |
| `summary` | object | yes | Aggregate counts summarizing the discovery results. |