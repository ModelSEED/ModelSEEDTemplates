# SEED Ontology Properties Documentation

## Overview

The SEED unified ontology uses custom properties to encode metabolic relationships between genes, roles, complexes, and reactions.

## Core Properties

### 1. enables_reaction
**URI**: `https://modelseed.org/ontology/enables_reaction`  
**Domain**: Role  
**Range**: Reaction  
**Cardinality**: Many-to-many

**Definition**: A role enables a reaction when it provides essential catalytic function (triggering=1).

**Example**:
```rdf
seed.role:0000000001234 enables_reaction seed.reaction:rxn00001
```

**Critical Rule**: Only roles marked as `triggering=1` in template complexes create this relationship.

**Count**: 6,348 relationships in production

---

### 2. has_role
**URI**: `https://modelseed.org/ontology/has_role`  
**Domain**: Complex  
**Range**: Role  
**Cardinality**: Many-to-many

**Definition**: A complex has a role as a component (non-optional roles only).

**Example**:
```rdf
seed.complex:cpx00123 has_role seed.role:0000000001234
```

**Rule**: Created for all roles where `optional_role=0` in complex definition.

**Count**: 6,347 relationships in production

---

### 3. has_complex
**URI**: `https://modelseed.org/ontology/has_complex`  
**Domain**: Reaction  
**Range**: Complex  
**Cardinality**: Many-to-many

**Definition**: A reaction is catalyzed by a complex.

**Example**:
```rdf
seed.reaction:rxn00001 has_complex seed.complex:cpx00123
```

**Count**: 4,554 relationships in production

---

### 4. reaction_type
**URI**: `https://modelseed.org/ontology/reaction_type`  
**Domain**: Reaction  
**Range**: String literal  
**Values**: "spontaneous" | "universal"

**Definition**: Marks reactions that occur without enzymes.

**Example**:
```rdf
seed.reaction:rxn00123 reaction_type "spontaneous"
```

**Count**: 42 reactions marked (31 spontaneous, 11 universal)

---

### 5. owl:sameAs
**URI**: `http://www.w3.org/2002/07/owl#sameAs`  
**Domain**: Role  
**Range**: Role  
**Type**: Symmetric, transitive

**Definition**: Links duplicate roles with identical function but different IDs.

**Example**:
```rdf
seed.role:0000000001234 owl:sameAs seed.role:0000000005678
```

**Critical**: Required for correct coverage calculation (99.81% vs 93.9%)

**Count**: 3,134 equivalence relationships

---

### 6. hasNormalizedForm
**URI**: `https://modelseed.org/ontology/hasNormalizedForm`  
**Domain**: Role  
**Range**: String literal  
**Purpose**: Performance optimization

**Definition**: Stores normalized role name for fast matching.

**Example**:
```rdf
seed.role:0000000001234 hasNormalizedForm "dnapolymeraseiiisubunitalpha"
```

**Normalization**: Lowercase, remove non-alphanumeric, strip whitespace

## Property Relationships

### Reaction Enablement Chain
```
Gene --maps_to--> Role --enables_reaction--> Reaction
                    |
                    +--part_of--> Complex --catalyzes--> Reaction
```

### Critical Logic Rules

1. **Triggering Constraint**:
   ```
   IF role.triggering = 1 AND role ∈ complex
   THEN role enables_reaction reaction
   ```

2. **Complex Satisfaction**:
   ```
   IF ∃role ∈ complex WHERE role.triggering = 1 AND gene_maps_to(role)
   THEN reaction_enabled
   ```

3. **Equivalence Expansion**:
   ```
   IF gene_maps_to(role1) AND role1 owl:sameAs role2
   THEN gene_maps_to(role2)
   ```

## Comparison with ModelSEEDpy

| Property | Our Ontology | ModelSEEDpy |
|----------|--------------|-------------|
| Triggering roles only | ✅ Yes | ❌ No (bug: allows optional) |
| owl:sameAs expansion | ✅ Yes | ✅ Yes (implicit) |
| Reaction types | ✅ Explicit property | ✅ Template field |
| Complex satisfaction | All triggering roles | Any role present |
| Coverage result | 99.81% | 99.9% |

## Query Examples

### Find all reactions enabled by a gene
```sql
WITH gene_roles AS (
    SELECT seed_role_id FROM term_associations 
    WHERE gene_id = 'gene_123'
),
equivalent_roles AS (
    SELECT object as role FROM statements 
    WHERE predicate = 'owl:sameAs' 
    AND subject IN (SELECT * FROM gene_roles)
    UNION
    SELECT seed_role_id as role FROM gene_roles
)
SELECT DISTINCT object as reaction
FROM statements
WHERE predicate = '<https://modelseed.org/ontology/enables_reaction>'
AND subject IN (SELECT * FROM equivalent_roles);
```

### Find spontaneous reactions
```sql
SELECT subject as reaction
FROM statements
WHERE predicate = '<https://modelseed.org/ontology/reaction_type>'
AND object = 'spontaneous';
```

## Implementation Notes

1. **URIs vs CURIEs**: Database stores full URIs, not prefixed forms
2. **String literals**: reaction_type uses plain strings, not URIs
3. **Performance**: hasNormalizedForm enables 100x faster lookups
4. **Completeness**: All properties are materialized, not inferred

## Statistics Summary

| Property | Count |
|----------|-------|
| enables_reaction | 6,348 |
| has_role | 6,347 |
| has_complex | 4,554 |
| reaction_type | 42 |
| owl:sameAs | 3,134 |
| Total relationships | 20,425 |

This represents a complete semantic encoding of metabolic reconstruction logic with 99.81% coverage.