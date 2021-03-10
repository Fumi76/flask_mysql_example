import configparser
import re
import mysql.connector.pooling as mysqldb
import time
import threading
import os

config = configparser.ConfigParser()
config.read('config.ini')
db_config = config['mysql']
print(db_config["use_unicode"], type(db_config["use_unicode"]))
print(db_config["charset"])

# use_unicodeはデフォルトTrue
dbconfig = {
  "database": db_config["database"],
  "user":     db_config["user"],
  "password": db_config["password"],
  "host": db_config["host"],
  "charset": db_config["charset"]
}

env_conn_pool_size = 20
if 'CONN_POOL_SIZE' in os.environ:
    env_conn_pool_size = os.environ['CONN_POOL_SIZE']
    print(env_conn_pool_size, type(env_conn_pool_size))
    # strとのこと
    p = re.compile("[0-9]+")
    m = p.fullmatch(env_conn_pool_size)
    if m is not None:
        env_conn_pool_size = int(env_conn_pool_size)
        print(env_conn_pool_size)
    else:
        raise Exception('CONN_POOL_SIZEは整数')

mysqldb.CNX_POOL_MAXSIZE = env_conn_pool_size

cnxpool = mysqldb.MySQLConnectionPool(pool_name = "mypool",
                                      pool_size = env_conn_pool_size,
                                      **dbconfig)

#
# テーブルにある値がなければレコード追加のパターンの検証
#
def test1():

    """
    conns = []
    for i in range(101):
        conn = cnxpool.get_connection()
        conns.append(conn)
        print(i+1)
    """

    conn = cnxpool.get_connection()
    cur = conn.cursor(dictionary=True)

    #sql = "select count(*) as cnt from dummy1 where id = 53 for update"
    #cur.execute(sql)
    # t2のselectとは関係しないカラムでfor updateしたがt2はブロックされた
    sql = "select count(*) as cnt from dummy1 where name = %s and category_id = 5 for update"
    cur.execute(sql, ["DDD"])
    print("t1 dummy1 DDD", cur.fetchone()['cnt'])
    # selectだとt2はブロックしない

    print("t1 sleep...")
    time.sleep(5)

    sql = "insert into dummy1 (name, category_id) value (%s, %s)"
    cur.execute(sql, ["あああ", 5])
    id = cur.lastrowid
    print("t1 rowcount", cur.rowcount)

    conn.commit()
    print("t1 commit")
    
    cur.execute("select * from dummy1 where id = %s", [id])
    row = cur.fetchone()
    print(row)

def test2():
    time.sleep(2)
    conn = cnxpool.get_connection()

    cur = conn.cursor(dictionary=True)

    sql = "select count(*) as cnt from dummy1 where id = 2 for update"
    print("t2 before select")
    cur.execute(sql)
    # id=2の場合、t1がid=53と別々の行の場合、t2はここでブロックしなかった
    # t1がnameとcategory_idの条件のとき、t2はidの条件でもブロックした

    #sql = "select count(*) as cnt from dummy1 where name = %s and category_id = 1 for update"
    #print("t2 before select")
    #cur.execute(sql, ["AAA"])
    print("t2 dummy1 AAA", cur.fetchone()['cnt'])
    # t2もselect for updateにすればここでブロックされる
    # category_id = 6とt1と別の値にしたがブロックされた
    # name=AAA, category_id=1と全く別の値にしたがブロックされた
    # t1がid=53でt2が別のカラムの条件のselectだったがブロックされた

    query = ("insert into dummy1(name, category_id)values(%s, %s)")
    print("t2 before insert")    
    cur.execute(query, ["DDD", 6])
    print("t2 before commit", cur.rowcount)
    conn.commit()
    print("t2 after commit")

t1 = threading.Thread(target=test1)
t2 = threading.Thread(target=test2)

t1.start()
t2.start()
