import configparser
import mysql.connector as mysqldb
import time
import threading

config = configparser.ConfigParser()
config.read('config.ini')
db_config = config['mysql']
print(db_config["use_unicode"], type(db_config["use_unicode"]))
print(db_config["charset"])

def test1():

    conn = mysqldb.connect(user=db_config["user"]
                        , password=db_config["password"],
                              host=db_config["host"],
                              database=db_config["database"])

    conn.start_transaction(consistent_snapshot=True,
                      isolation_level='SERIALIZABLE',
                      readonly=False)

    cur = conn.cursor(dictionary=True)

    """
    # 先にselectしておいてみる
    sql = "select * from dummy1 where name = %s"
    cur.execute(sql, ["BBB"])
    print("t1 select dummy1 BBB", cur.fetchall())
    """

    # select for update
    sql = "select * from dummy1 where name = %s for update"
    cur.execute(sql, ["BBB"])
    print("t1 select for update dummy1 BBB", cur.fetchall())

    print("t1 sleep...")
    time.sleep(10)

    print("t1 before update dummy1 BBB")
    sql = "update dummy1 set name = %s where name = %s"
    cur.execute(sql, ["BBB1", "BBB"])
    print("t1 update dummy1 BBB", cur.rowcount)
    # ここでデッドロックが発生する
    # t2がt1に関係ないレコード(同じテーブル)を参照していてもデッドロック発生する
    # REPEATABLE READだと、デッドロックは起きないが、
    # ここのrowcountは0になる（t2により変更されていてその変更が見えてしまう）

    conn.commit()
    print("t1 commit")
    

def test2():
    time.sleep(2)
    conn = mysqldb.connect(user=db_config["user"]
                        , password=db_config["password"],
                              host=db_config["host"],
                              database=db_config["database"])

    conn.start_transaction(consistent_snapshot=True,
                      isolation_level='SERIALIZABLE',
                      readonly=False)

    cur = conn.cursor(dictionary=True)
    
    """
    print("t2 before select dummy1 BBB")
    sql = "select * from dummy1 where name = %s"
    cur.execute(sql, ["BBB"])
    print("t2 select dummy1 BBB", cur.fetchall())
    # t1がselect for updateしていても取得できる
    """

    # t2もselect for update
    print("t2 before select for update dummy1 BBB")
    sql = "select * from dummy1 where name = %s for update"
    cur.execute(sql, ["BBB"])
    print("t2 select for update dummy1 BBB", cur.fetchall())
    # t1もselect for updateしていると待機になった

    """
    # t1に関係ないレコードのselect for update
    print("t2 before select for update dummy1 CCC")
    sql = "select * from dummy1 where name = %s for update"
    cur.execute(sql, ["CCC"])
    print("t2 select for update dummy1 CCC", cur.fetchall())
    # t1に関係ないレコードであってもselect for updateはブロックされる
    """

    query = ("update dummy1 set name = %s where name = %s")
    cur.execute(query, ["BBB2", "BBB"])
    print("t2 update dummy1 BBB", cur.rowcount)
    # t1がselect for updateしている行の更新は待機になる
    # かつ、t1の変更が見えるのでrowcount=0がありうる

    """
    # t1に関係ないレコードを更新する
    print("t2 before select dummy1 CCC")
    sql = "select * from dummy1 where name = %s"
    cur.execute(sql, ["CCC"])
    print("t2 select dummy1 CCC", cur.fetchall())
    """

    """
    query = ("update dummy1 set name = %s where name = %s")
    cur.execute(query, ["CCC2", "CCC"])
    print("t2 update dummy1 CCC", cur.rowcount)
    # 関係ないレコードであってもブロックされる
    """

    conn.commit()
    print("t2 commit")


t1 = threading.Thread(target=test1)
t2 = threading.Thread(target=test2)

t1.start()
t2.start()
