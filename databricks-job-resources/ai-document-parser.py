# Databricks notebook source
dbutils.widgets.text("ai_parse_document_output_table", "fouad_demos.information_extraction.ai_parse_document_output", "AI parse document output table")
dbutils.widgets.text("partition_count", "8", "Partition Count")
dbutils.widgets.text("source_volume_path", "", "Source Volume Path")


# COMMAND ----------

ai_parse_document_output_table = dbutils.widgets.get("ai_parse_document_output_table")
parallelism = dbutils.widgets.get("partition_count")
source_volume_path = dbutils.widgets.get("source_volume_path")

import pandas as pd

params_df = pd.DataFrame([
    {"Parameter": "ai_parse_document_output_table", "Value": ai_parse_document_output_table},
    {"Parameter": "parallelism", "Value": parallelism},
    {"Parameter": "source_volume_path", "Value": source_volume_path}
])

display(params_df)

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS IDENTIFIER(:ai_parse_document_output_table)(
# MAGIC   path STRING,
# MAGIC   file_content_checksum STRING,
# MAGIC   raw_parsed VARIANT,
# MAGIC   text STRING,
# MAGIC   format_supported BOOLEAN,
# MAGIC   error_status STRING,
# MAGIC   created_at TIMESTAMP,
# MAGIC   updated_at TIMESTAMP
# MAGIC )
# MAGIC

# COMMAND ----------

supported_formats = ",".join(["'.pdf'", "'.jpg'", "'.jpeg'", "'.png'","'.doc'","'.ppt'"])
spark.sql(f"""
WITH all_files AS (
  SELECT
    path,
    md5(content) as file_content_checksum,
    content,
    current_timestamp() created_at,
    current_timestamp() updated_at
  FROM
    READ_FILES('{source_volume_path}', format => 'binaryFile')
),
to_process AS (
  SELECT 
    new.*
  FROM 
    all_files new LEFT ANTI JOIN {ai_parse_document_output_table} existing 
  ON new.file_content_checksum = existing.file_content_checksum
),
repartitioned_files AS (
  SELECT 
    *
  FROM 
    to_process
  DISTRIBUTE BY 
    crc32(path) % {parallelism}
),
parsed_documents AS (
  SELECT
    *,
    ai_parse_document(content) as parsed,
    true as format_supported
  FROM
    repartitioned_files
  WHERE array_contains(array({supported_formats}), lower(regexp_extract(path, r'(\\.[^.]+)$', 1)))
),
raw_documents AS (
  SELECT
    path,
    file_content_checksum,
    null as raw_parsed,
    decode(content, 'utf-8') as text,
    false as format_supported,
    null as error_status,
    created_at,
    updated_at
  FROM 
    repartitioned_files
  WHERE NOT array_contains(array({supported_formats}), lower(regexp_extract(path, r'(\\.[^.]+)$', 1)))
),
error_documents AS (
  SELECT
    path,
    file_content_checksum,
    parsed as raw_parsed,
    null as text,
    format_supported,
    try_cast(parsed:error_status AS STRING) AS error_status,
    created_at,
    updated_at
  FROM
    parsed_documents
  WHERE try_cast(parsed:error_status AS STRING) IS NOT NULL
),
sorted_contents AS (
  SELECT
    file_content_checksum,
    element:content AS content
  FROM
    (
      SELECT
        file_content_checksum,
          posexplode(
            CASE
              WHEN try_cast(parsed:metadata:version AS STRING) = '1.0' 
              THEN try_cast(parsed:document:pages AS ARRAY<VARIANT>)
              ELSE try_cast(parsed:document:elements AS ARRAY<VARIANT>)
            END
          ) AS (idx, element)
      FROM
        parsed_documents
      WHERE try_cast(parsed:error_status AS STRING) IS NULL
    )
  ORDER BY
    idx
),
concatenated AS (
    SELECT
        file_content_checksum,
        concat_ws('\n\n', collect_list(content)) AS full_content
    FROM
        sorted_contents
    WHERE content IS NOT NULL
    GROUP BY
        file_content_checksum
),
with_raw AS (
    SELECT
        b.path,
        b.file_content_checksum,
        b.parsed as raw_parsed,
        a.full_content as text,
        b.format_supported,
        null as error_status,
        b.created_at,
        b.updated_at
    FROM 
      concatenated a
    JOIN parsed_documents b ON a.file_content_checksum = b.file_content_checksum
)
SELECT *  FROM with_raw
UNION ALL 
SELECT * FROM raw_documents
UNION ALL
SELECT * FROM error_documents
""").createOrReplaceTempView("documents_processed")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- TODO : incorporate the updated_at column when you implement force_rerun
# MAGIC MERGE INTO IDENTIFIER(:ai_parse_document_output_table) AS target
# MAGIC USING documents_processed AS source
# MAGIC ON target.file_content_checksum = source.file_content_checksum
# MAGIC WHEN NOT MATCHED THEN
# MAGIC   INSERT *
# MAGIC

# COMMAND ----------

df = spark.sql(f"""
SELECT 
  regexp_replace(path, '^dbfs:', '') as path,
  md5(content) as file_content_checksum
FROM
  READ_FILES('{source_volume_path}', format => 'binaryFile')
""")

from pyspark.sql.functions import to_json, collect_list, struct

df_json = df.agg(to_json(collect_list(struct("*"))).alias("json_array"))
result = df_json.collect()[0]['json_array']

# COMMAND ----------

dbutils.notebook.exit(result)