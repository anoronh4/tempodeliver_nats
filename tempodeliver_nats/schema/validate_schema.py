import jsonschema, json

def validate_schema(schema_json, meta_json):
    with open(schema_json,'r') as fh:
        schema = json.load(fh)
    with open(meta_json,'r') as fh:
        meta = json.load(fh)
    jsonschema.validators.validate(instance=meta, schema=schema)

validate_schema("qc-complete.schema.json","qc-complete.example.json")
validate_schema("maf-complete.schema.json","maf-complete.example.json")
validate_schema("bam-complete.schema.json","bam-complete.example.json")
validate_schema("cohort-complete.schema.json","cohort-complete.example.json")