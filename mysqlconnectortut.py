>>> conn = mysql.connector.connect(host='localhost', database='wb7exnet_wb7eux', user='wb7eux_db', password='w')

>>> cursor = conn.cursor()

>>> cursor.execute("select * from quotations")

>>> rows = cursor.fetchall()

>>> print(cursor.rowcount)

>>> for row in rows:
>>>   print(row)


from mysql.connector import MySQLConnection, Error
from python_mysql_dbconfig import read_db_config
 
 
def query_with_fetchall():
    try:
        dbconfig = read_db_config()
        conn = MySQLConnection(**dbconfig)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books")
        rows = cursor.fetchall()
 
        print('Total Row(s):', cursor.rowcount)
        for row in rows:
            print(row)
 
    except Error as e:
        print(e)
 
    finally:
        cursor.close()
        conn.close()
 
 
if __name__ == '__main__':
    query_with_fetchall()
