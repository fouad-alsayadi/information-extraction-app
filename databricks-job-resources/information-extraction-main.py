# Databricks notebook source
dbutils.widgets.text("job_id", "", "Analysis Job ID")
dbutils.widgets.text("schema_id", "", "Schema ID")
job_id = dbutils.widgets.get("job_id")
schema_id = dbutils.widgets.get("schema_id")
print(f"Using job_id: {job_id}, schema_id: {schema_id}")

# COMMAND ----------

# MAGIC %run ./postgres_client_util

# COMMAND ----------


upload_directory = execute_query(f"select upload_directory from {job_conf['lakebase_schema_name']}.extraction_jobs where id = {job_id}", fetch_all=True)[0]['upload_directory']

# COMMAND ----------

parse_job_output = dbutils.notebook.run("./ai-document-parser", 0, {
  "ai_parse_document_output_table": job_conf['ai_parse_document_output_table'],
  "source_volume_path" : upload_directory
  })

# COMMAND ----------

import json
documents_parsed = json.loads(parse_job_output)

# COMMAND ----------

documents_info = execute_query(f"""
                               SELECT 
                                * 
                               FROM 
                                {job_conf['lakebase_schema_name']}.documents 
                               WHERE 
                                job_id = {job_id}""", fetch_all=True
                              )

# COMMAND ----------

import pandas as pd
documents_info = pd.DataFrame(documents_info)
paths_md5 = pd.DataFrame(documents_parsed)

# COMMAND ----------

documents_metadata = documents_info.merge(paths_md5, left_on='file_path', right_on='path', how='inner').drop(columns=['path'])
display(documents_metadata)

# COMMAND ----------


extraction_schema = execute_query(f"select fields from {job_conf['lakebase_schema_name']}.extraction_schemas where id = {schema_id}", fetch_all=True)[0]['fields']

# COMMAND ----------

import json

schema_list = json.loads(extraction_schema)
items = []
items_str = []
for obj in schema_list:
    obj.pop('id', None)
    obj.pop('type', None)
    obj.pop('required', None)
    if 'name' in obj:
        obj['element_to_extract'] = obj.pop('name')
    element = obj.get('element_to_extract', '')
    description = obj.get('description', '')
    items.append(obj)
    items_str.append(f"{element}: {description}")
elements_to_extract = "\n".join(items_str)
elements_to_extract
items

# COMMAND ----------

propmpt  = f"""
please only extract the following information ( do not extract any other information ) and return the results as a simple json format without backticks or 'json' keyword : \n {items}  \n the content here : 
"""
propmpt

# COMMAND ----------

document_metadata_spark = spark.createDataFrame(documents_metadata)
document_metadata_spark.createOrReplaceTempView('documents_metadata')
display(document_metadata_spark)

# COMMAND ----------

documents_md5 = ",".join([ f"'{e['file_content_checksum']}'" for e in documents_parsed])
escaped_prompt = json.dumps(propmpt)
inference = spark.sql(f"""
SELECT 
  
  {job_id} as job_id,
  {schema_id} as schema_id,
  m.id as document_id,
  ai_query('databricks-claude-sonnet-4', CONCAT({escaped_prompt}, raw_parsed)) AS extracted_data,
  p.file_content_checksum
FROM 
  {job_conf['ai_parse_document_output_table']} p
JOIN documents_metadata m on p.file_content_checksum=m.file_content_checksum
WHERE
  p.file_content_checksum  in ({documents_md5})
""")
#
# inference_pdf = inference.toPandas()

# COMMAND ----------

rows = inference.toPandas().to_dict(orient='records')
display(rows)

# COMMAND ----------

table_name = f"{job_conf['lakebase_schema_name']}.extraction_results"
columns = list(rows[0].keys())
columns_str = ', '.join([f'"{col}"' for col in columns])
placeholders = ', '.join([f':{col}' for col in columns])
update_str = ', '.join([f'"{col}"=EXCLUDED."{col}"' for col in columns if col not in ['document_id', 'job_id', 'schema_id']])

upsert_sql = (
    "INSERT INTO {} ({})\nVALUES ({})\nON CONFLICT (document_id, job_id, schema_id)\nDO UPDATE SET {}".format(
        table_name, columns_str, placeholders, update_str
    )
)


# COMMAND ----------

for row in rows:
    row_map = dict(row)
    execute_commit_statement(upsert_sql,row_map)