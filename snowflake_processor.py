import pandas as pd
import snowflake.connector
from pandasai.smart_dataframe import SmartDataframe


def process_snowflake_data(sf_user,sf_password):
    # Connect to Snowflake
    # conn = snowflake.connector.connect(
    #     user='SOUVIKGANGULY',
    #     password='QGPassword123!',
    #     account='zo11777.central-india.azure',
    #     database= "QG_Sample_DB",
    #     warehouse= "COMPUTE_WH",
    #     schema= "QG_SCHEMA_SAMPLE",
    #     role = "ACCOUNTADMIN"
    # )
    conn = snowflake.connector.connect(
        user= sf_user,
        password= sf_password,
        account= 'mp27686.central-india.azure',
        database= "QG_SAMPLE_DB",
        warehouse= "COMPUTE_WH",
        schema= "QG_SCHEMA_SAMPLE",
        role = "ACCOUNTADMIN"
    )

    cur = conn.cursor()

    # Query data into a Pandas DataFrame
    query = f"SHOW TABLES IN SCHEMA QG_SAMPLE_DB.QG_SCHEMA_SAMPLE"
    cur.execute(query)
    # df = pd.read_sql(query, conn)
    # Fetch results
    tables = [row[1] for row in cur.fetchall()]

    #convert pandas df to smartdf
    # df = SmartDataframe(df)
    print(tables)
    return tables, conn