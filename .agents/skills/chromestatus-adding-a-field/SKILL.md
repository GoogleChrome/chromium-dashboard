---
name: chromestatus-adding-a-field
description: How to add a new field to a feature across the entire stack (Data, API, and Frontend).
---

# Adding a Field to a Feature

This guide explains how to add a new field to a feature entry, ensuring it is properly persisted in the database, exposed via the API, and editable in the frontend.

## 1. Data Layer (Backend)

The primary data model for features is `FeatureEntry` located in `internals/core_models.py`.

### Add Property to `FeatureEntry`
Add your new field as an `ndb` property.

```python
# internals/core_models.py

class FeatureEntry(ndb.Model):
  # ...
  my_new_field = ndb.StringProperty()  # Use appropriate ndb type (IntegerProperty, BooleanProperty, etc.)
```

## 2. API Layer (Backend)

### Update `api_specs.py`
The `FeaturesAPI` uses `api/api_specs.py` to map request fields to database properties and handle types.

```python
# api/api_specs.py

FEATURE_FIELD_DATA_TYPES: FIELD_INFO_DATA_TYPE = [
  # ...
  ('my_new_field', 'str'),  # 'str', 'int', 'bool', 'link', 'emails', etc.
]
```

### Update Converters (Optional)
If your field needs custom formatting for the JSON response (e.g., date to string), update `api/converters.py`. Most simple types are handled automatically by `to_dict`.

```python
# api/converters.py

def feature_entry_to_json_verbose(fe: FeatureEntry, ...):
    # ...
    d: VerboseFeatureDict = {
        # ...
        'my_new_field': fe.my_new_field,
    }
```

## 3. OpenAPI Specification

Update `openapi/api.yaml` if you want the field to be part of the official API documentation and generated models.

```yaml
# openapi/api.yaml
# (Find the relevant schema, e.g., Feature or FeatureEntry if exists, 
# or update the endpoint response descriptions)
```

## 4. Frontend Layer

### Define Form Field Metadata
Add the field's metadata (label, help text, component type) in `client-src/elements/form-field-specs.ts`.

```typescript
// client-src/elements/form-field-specs.ts

export const ALL_FIELDS: Record<string, Field> = {
  // ...
  my_new_field: {
    type: 'input', // 'textarea', 'checkbox', 'select', etc.
    attrs: TEXT_FIELD_ATTRS,
    label: 'My New Field',
    usage: ALL_INTENT_USAGE_BY_FEATURE_TYPE,
    help_text: html`Explain what this field is for.`,
  },
};
```

### Add to Form Definitions
Include the field in the relevant forms in `client-src/elements/form-definition.ts`.

```typescript
// client-src/elements/form-definition.ts

export const FLAT_METADATA_FIELDS: MetadataFields = {
  name: 'Feature metadata',
  sections: [
    {
      name: 'Feature metadata',
      fields: [
        // ...
        'my_new_field',
      ],
    },
  ],
};
```

## 5. Verification

1. **Backend**: Run `npm test` to ensure NDB properties and converters work.
2. **Frontend**: Run `npm run webtest` or manually verify the new field appears in the feature edit form.
3. **API**: Manually check `/api/v0/features/{id}` to see if the field is present.
