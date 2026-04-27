"""Knowledge graph architecture for structured AI memory.

Layers
------
Entity      : KnowledgeNode with typed EntityType
Relationship: Triple (subject -> predicate -> object)
Evidence    : provenance per triple (source, timestamp, confidence)
Permission  : PrivacyLevel + PermissionMask per node
Audit       : append-only AuditLog of all mutations
Cluster     : connected components and pattern mining
Retrieval   : k-hop search and bounded AI context building
"""

from .audit import AuditEvent, AuditLog
from .cluster import (
    Cluster,
    RelationshipPattern,
    build_subgraph,
    detect_patterns,
    find_connected_components,
)
from .extractor import extract_graph_from_repos
from .graph import KnowledgeGraph
from .models import (
    EntityType,
    Evidence,
    KnowledgeNode,
    PermissionMask,
    PrivacyLevel,
    Triple,
)
from .retrieval import GraphRetriever, QueryResult

__all__ = [
    "AuditEvent",
    "AuditLog",
    "build_subgraph",
    "Cluster",
    "detect_patterns",
    "EntityType",
    "Evidence",
    "extract_graph_from_repos",
    "find_connected_components",
    "GraphRetriever",
    "KnowledgeGraph",
    "KnowledgeNode",
    "PermissionMask",
    "PrivacyLevel",
    "QueryResult",
    "RelationshipPattern",
    "Triple",
]
