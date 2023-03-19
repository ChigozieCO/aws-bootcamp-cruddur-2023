from psycopg_pool import ConnectionPool
import os
import re
import sys

class db:
  def __init__(self):
    self.init_pool()

  def template(name):

  def init_pool(self):
    connection_url = os.getenv("CONNECTION_URL")
    self.pool = ConnectionPool(connection_url)
  # We want to commit query such as an insert
  def query_commit(self,sql,params):
    # be sure to check for RETURNING in all uppercases
    print("SQL STATEMENT [commit with returning id] -----------")

    pattern = r"\bRETURNING\b"
    is_returning_id = re.search(pattern, sql)

    try:
      conn = self.pool.connection()
      cur = conn.cursor()
      cur.execute(sql,params)
      if is_returning_id:
        returning_id = cur.fetchone()[0]
        conn.commit() 
      if is_returning_id:
        return returning_id
    except Exception as err:
      self.print_sql_err(err)
  # when we want to return a json object
  def query_array_json(self,sql):
    print("SQL STATEMENT [array] -----------")
    print(sql + "\n")
    wrapped_sql = self.query_wrap_array(sql)
    with self.pool.connection() as conn:
      with conn.cursor() as cur:
        cur.execute(wrapped_sql)
        json = cur.fetchone()
        return json[0]
  # when we want to return an array of json objects
  def query_object_json(self,sql):
    print("SQL STATEMENT [object] -----------")
    print(sql + "\n")
    wrapped_sql = self.query_wrap_object(sql)
    with self.pool.connection() as conn:
      with conn.cursor() as cur:
        cur.execute(wrapped_sql)
        json = cur.fetchone()
        return json[0]
  
  def query_wrap_object(self,template):
    sql = f"""
    (SELECT COALESCE(row_to_json(object_row),'{{}}'::json) FROM (
    {template}
    ) object_row);
    """
    return sql
  def query_wrap_array(self,template):
    sql = f"""
    (SELECT COALESCE(array_to_json(array_agg(row_to_json(array_row))),'[]'::json) FROM (
    {template}
    ) array_row);
    """
    return sql
  def print_sql_err(self,err):
    # get details about the exception
    err_type, err_obj, traceback = sys.exc_info()

    # get the line number when exception occured
    line_num = traceback.tb_lineno

    # print the connect() error
    print ("\npsycopg ERROR:", err, "on line number:", line_num)
    print ("psycopg traceback:", traceback, "-- type:", err_type)

    # print the pgcode and pgerror exceptions
    print ("pgerror:", err.pgerror)
    print ("pgcode:", err.pgcode, "\n")