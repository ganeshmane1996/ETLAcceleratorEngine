import json

import mysql.connector as mysql
from pyspark.sql import SparkSession
from pyspark.sql.functions import when, col
from pyspark.sql.types import StructField, StructType, BooleanType, DoubleType, StringType, IntegerType

spark = SparkSession.builder \
    .appName("healthCare data") \
    .getOrCreate()


def data_schema(config):
    schema = config['Schema']
    field_list = []
    for column in schema['columns']:
        if (column['datatype']) == 'Integer':
            fields = StructField(column['name'], IntegerType(), True)
        elif (column['datatype']) == 'String':
            fields = StructField(column['name'], StringType(), True)
        elif (column['datatype']) == 'Double':
            fields = StructField(column['name'], DoubleType(), True)
        elif (column['datatype']) == 'Boolean':
            fields = StructField(column['name'], BooleanType(), True)
        field_list.append(fields)
    return StructType(field_list)


def source(config, schema):
    if config['Input']['format'] == 'file':
        path = config['Input']['path']
        Input_Format = config['Input']['type']
        healthCare_data = spark.read \
            .format(Input_Format) \
            .option('header', True) \
            .schema(schema) \
            .load(path)
        return healthCare_data
    elif config['Input']['format'] == "database":
        dbtype = config['Input']['type']
        hostname = config['Input']['hostname']
        user = config['Input']['username']
        password = config['Input']['password']
        database = config['Input']['dbname']
        table = config['Input']['table']
        jdbcDF = spark.read.format("jdbc") \
            .option("url", f"jdbc:{dbtype}://{hostname}:/{database}") \
            .option("dbtable", table) \
            .option("user", user) \
            .option("password", password) \
            .load()
        return jdbcDF


def generate_dataframe(dataframe, operations,config):
    column_names = config['Display_column']['display_columns']
    if len(operations) == 0:
        return dataframe
    else:
        select_clause = "SELECT "
        where_clause = "WHERE"
        operation = operations[0]
        operator_type = operation['operation_type']
        conditional_column = operation['column']
        conditional_operator = operation['operator']
        values = operation['value']
        dataframe.createOrReplaceTempView("data")

        if operator_type == "filter":
            query = select_clause
            query += "{} ".format(",".join(column_names))
            query += "FROM {} ".format("data")
            query += "{} ".format(where_clause)
            query += "{} {} {}".format(conditional_column, conditional_operator, values)
        elif operator_type == 'when then':
            new_col = operation["new_col"]
            new_val = operation["new_val"]
            if isinstance(values, list):
                conditional_value_str = '(' + ','.join([f"'{val}'" for val in values]) + ')'
                query = select_clause
                query += "{}".format(",".join(column_names))
                query += ",CASE WHEN {} {} {} THEN {} ELSE {} END AS {} ".format(conditional_column,
                                                                                 conditional_operator,
                                                                                 conditional_value_str,
                                                                                 conditional_column, new_val, new_col)
                query += " FROM {}".format("data")
            else:
                query = select_clause
                query += "{}".format(",".join(column_names))
                query += ",CASE WHEN {} {} {} THEN {} ELSE {} END AS {} ".format(conditional_column,
                                                                                 conditional_operator,
                                                                                 values, conditional_column,
                                                                                 new_val, new_col)
                query += " FROM {}".format("data")
        new_dataframe = spark.sql(query)
        new_dataframe.createOrReplaceTempView("data")
        return generate_dataframe(new_dataframe, operations[1:], config)

# storing dataframe to [csv,mysql] any one of them ...


def destination(config, dataframe):
    if config['Output']['format'] == 'file':
        path = config['Output']['path']
        format = config['Output']['type']
        header = config['Output']['header']
        dataframe.write.format(format).save(path,header = header)
        print('successfully written to csv !!')
    elif config['Output']['format'] == 'database':
        dbtype = config['Output']['type']
        hostname = config['Output']['hostname']
        user = config['Output']['username']
        password = config['Output']['password']
        database = config['Output']['dbname']
        table = config['Output']['table']
        database_name = config['Output']['dbname']
        conn = mysql.connect(host=hostname, user=user, password=password)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        dataframe.write.format('jdbc') \
                       .options(
                                  url=f'jdbc:{dbtype}://{hostname}/{database}',
                                  dbtable=table,
                                  user=user,
                                  password=password
                                 )\
                       .mode('overwrite').save()
        print('successfully written to database !!')







