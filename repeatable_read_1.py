import configparser
import mysql.connector as mysqldb
import time
import threading

config = configparser.ConfigParser()
config.read('config.ini')
db_config = config['mysql']
print(db_config["use_unicode"], type(db_config["use_unicode"]))
print(db_config["charset"])

#
# テーブルにある値がなければレコード追加のパターンの検証
#
def test1():

    conn = mysqldb.connect(user=db_config["user"]
                        , password=db_config["password"],
                              host=db_config["host"],
                              database=db_config["database"])

    cur = conn.cursor(dictionary=True)

    #sql = "select count(*) as cnt from dummy1 where id = 53 for update"
    #cur.execute(sql)
    # t2のselectとは関係しないカラムでfor updateしたがt2はブロックされた
    sql = "select count(*) as cnt from dummy1 where name = %s and category_id = 5 for update"
    cur.execute(sql, ["DDD"])
    print("t1 dummy1 DDD", cur.fetchone()['cnt'])
    # selectだとt2はブロックしない

    print("t1 sleep...")
    time.sleep(10)

    sql = "insert into dummy1 (name, category_id) value (%s, %s)"
    cur.execute(sql, ["DDD", 5])
    print("t1 rowcount", cur.rowcount)

    conn.commit()
    print("t1 commit")
    

def test2():
    time.sleep(2)
    conn = mysqldb.connect(user=db_config["user"]
                        , password=db_config["password"],
                              host=db_config["host"],
                              database=db_config["database"])

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
