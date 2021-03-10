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

    """                          
    conn.autocommit = False
    
    conn.start_transaction(consistent_snapshot=True,
                      isolation_level='SERIALIZABLE',
                      readonly=False)
    # autocommitはデフォルトでFalse
    # トランザクションレベルを変えてもtimestampの値は都度変わる
    """

    cur = conn.cursor(dictionary=True)

    #cur.execute("SET SESSION timestamp = UNIX_TIMESTAMP()")
    cur.execute("SET @start = now()")
    cur.execute("SELECT @start")
    print(cur.fetchone())

    #query = ("insert into dummy1(name, category_id, ts)values(%s, %s, now())")
    query = ("insert into dummy1(name, category_id, ts)values(%s, %s, @start)")
    cur.execute(query, ["XXX", 1])
    conn.commit()
    print("insert to dummy1 done.")

    time.sleep(5)

    #query = ("insert into dummy1(name, category_id, ts)values(%s, %s, now())")
    query = ("insert into dummy1(name, category_id, ts)values(%s, %s, @start)")
    cur.execute(query, ["YYY", 1])
    conn.commit()
    print("insert to dummy1 done.")

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
#t2 = threading.Thread(target=test2)

t1.start()
#t2.start()
