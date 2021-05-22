import configparser
import mysql.connector as mysqldb
import time
import threading

config = configparser.ConfigParser()
config.read('config.ini')
db_config = config['mysql']
# print(db_config["use_unicode"], type(db_config["use_unicode"]))
# print(db_config["charset"])

def test1():

    conn = mysqldb.connect(user=db_config["user"]
                        , password=db_config["password"],
                              host=db_config["host"],
                              database=db_config["database"])

    """
    conn.start_transaction(consistent_snapshot=True,
                           isolation_level='SERIALIZABLE',
                           readonly=False)
    """

    cur = conn.cursor(dictionary=True)

    #print('T1 lock table...')
    #cur.execute("LOCK TABLES dummy1 WRITE")
    #print('T1 lock table done')

    # name は varchar(100)
    # select id でも select count(*) as num でも同じ結果
    
    print('T1 select for update...')
    sql = "select count(*) as num from dummy1 where name = %s for update"
    cur.execute(sql, ["BBB"])
    #sql = "select * from dummy1 where category_id = %s for update"
    #cur.execute(sql, [1])
    print('T1 select for update done')
    result = cur.fetchone()
    print("T1", result)
    print('T1 sleep1...')
    time.sleep(10)
    print('T1 sleep1 done')
    #if result is None:
    if result['num'] == 0:
        sql = "insert into dummy1 (name, category_id) values ('BBB', 1)"
        cur.execute(sql, [])
        print('T1 insert rowcount', cur.rowcount)
        cur.execute("select * from dummy1 where id = %s for update",
        [cur.lastrowid])
        cur.fetchone()
        print('T1 select for update by id done')
    
    #print('T1 unlock table...')
    #cur.execute("UNLOCK TABLES")
    #print('T1 unlock table done')

    print('T1 sleep...')
    time.sleep(10)
    print('T1 sleep done')
    conn.commit()
    print("T1 commit")
    

def test2():
    time.sleep(2)
    conn = mysqldb.connect(user=db_config["user"]
                        , password=db_config["password"],
                              host=db_config["host"],
                              database=db_config["database"])

    """
    conn.start_transaction(consistent_snapshot=True,
                           isolation_level='SERIALIZABLE',
                           readonly=False)
    """

    cur = conn.cursor(dictionary=True)

    # print('T2 lock table...')
    # cur.execute("LOCK TABLES dummy1 WRITE")
    # print('T2 lock table done')

    # select id でも select count(*) as num でも select * でも同じ結果
    # 片方が select id で、もう片方が select count(*) でも同じ結果
    # テーブルに該当レコードがない時点（あるいは、テーブルが空）でも、ロック待ちになる
    # テーブルに条件に関係ないレコードがあっても、同じ挙動
    # T1 がロックしたBBBと関係ない DDDの行をロックしようとしたら待ちになった
    # 主キー、ユニークキーで select ～ for update しないと、テーブル全体でロックになったり、ある程度の範囲でロックがかかったりする。とのこと
    # name じゃなくて int型のcategory_idでも同じ挙動
    
    sql = "select count(*) as num from dummy1 where name = %s for update"
    #sql = "select * from dummy1 where category_id = %s for update"
    print('T2 select for update...')
    cur.execute(sql, ["BBB"])
    #cur.execute(sql, [1])
    print('T2 select for update done')
    result = cur.fetchone()
    print("T2", result)
    #if result is None:
    if result['num'] == 0:
        sql = "insert into dummy1 (name, category_id) values ('BBB', 1)"
        cur.execute(sql, [])
        print('T2 insert rowcount', cur.rowcount)
    else:
        print('T2 No insert') 

    #print('T2 unlock table...')
    #cur.execute("UNLOCK TABLES")
    #print('T2 unlock table done')

    conn.commit()
    print("T2 commit")

t1 = threading.Thread(target=test1)
t2 = threading.Thread(target=test2)

t1.start()
t2.start()
