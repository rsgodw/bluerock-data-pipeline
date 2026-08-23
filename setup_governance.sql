USE DATABASE CREDIT_UNION_DB;
USE SCHEMA RAW;

-- 1. Create the Dynamic Masking Policy
CREATE OR REPLACE MASKING POLICY dynamic_pii_mask AS (val string) RETURNS string ->
  CASE
    WHEN CURRENT_ROLE() IN ('DATA_ENGINEER', 'ACCOUNTADMIN') THEN val
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('snowflake.core.semantic_category') = 'PHONE_NUMBER' 
      THEN '***-***-' || RIGHT(val, 4)
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('snowflake.core.semantic_category') = 'EMAIL' 
      THEN REGEXP_REPLACE(val, '^.*@', '***@')
    ELSE '***MASKED***'
  END;

-- 2. Globally bind the policy to the Snowflake semantic category tag
ALTER TAG snowflake.core.semantic_category SET MASKING POLICY dynamic_pii_mask;

-- 3. Trigger native payload classification on the target table
CALL SYSTEM$CLASSIFY('CREDIT_UNION_DB.RAW.MEMBERS', {'auto_tag': true});
