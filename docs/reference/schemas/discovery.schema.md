# DITA Package Discovery Contract

Stable discovery contract describing observable structure of a DITA package. Artifacts represent files, graph represents structural truth, and relationships are a backward-compatible projection of graph edges.

## Properties

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `artifacts` | array | yes | Complete inventory of discovered artifacts. |
| `relationships` | array | yes | Backward-compatible flat projection of graph.edges. |
| `graph` | object | yes |  |
| `summary` | object | yes | Aggregate structural metrics. |