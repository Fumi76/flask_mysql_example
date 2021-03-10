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

    cur = conn.cursor(dictionary=True)

    # 先にselectしておいてみる
    sql = "select * from dummy1 where name = %s for update"
    cur.execute(sql, ["BBB"])
    print("t1 dummy1 BBB 1回目", cur.fetchall())

    query = ("SELECT * FROM dummy1 where category_id = 1")
    cur.execute(query)
    rows = cur.fetchall()
    print("t1 dummy1 1回目", rows)    
    print("t1 sleep...")
    time.sleep(10)

    # 読み取りは一貫性があり、1回目と同じ結果となる
    cur.execute(query)
    rows = cur.fetchall()
    print("t1 dummy1 2回目", rows)

    # dummy2にはt2による更新とコミット後に初めてアクセスしているが、
    # その変更は見えない
    # このトランザクションが始まった時点以降の
    # 別のスレッドによる変更は、そのスレッドでコミットしていたとしても見えない
    cur.execute("select * from dummy2 where category_id = 1")
    print("t1 dummy2", cur.fetchall())

    # このスレッドはコミットせずにクローズ（おそらくロールバックされる？）

    # 相手がname=BBBを変更した
    cur.execute("select * from dummy1 where name = %s", ["BBB"])
    print("t1 dummy1 BBB 2回目", cur.fetchall())
    # ここは検索結果あり

    sql = "update dummy1 set name = %s where name = %s"
    cur.execute(sql, ["BBBb", "BBB"])
    print("t1 rowcount", cur.rowcount)
    # しかし更新したら、rowcount=0になった
    # 相手が更新する前にselectしたがダメだった
    # 相手が更新する前にselec for updateしたら、相手の更新は待機し、
    # rowcount=1になった

    sql = "update dummy2 set name = %s where name = %s"
    cur.execute(sql, ["CCCc", "CCC"])
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
    
    """
    query = ("insert into dummy1(name, category_id)values(%s, %s)")
    cur.execute(query, [threading.get_ident(), 1])
    conn.commit()
    print("insert to dummy1 done.")
    # 相手には見えない
    """

    """
    query = "delete from dummy1 where category_id = %s"
    cur.execute(query, [1])
    conn.commit()
    print("delete done.")
    # 相手には見えない
    """

    """
    query = ("insert into dummy2(name, category_id)values(%s, %s)")
    cur.execute(query, [threading.get_ident(), 1])
    conn.commit()
    print("insert to dummy2 done.")
    # 相手には見えない
    """

    """
    print("before 1st update in t2...")
    query = ("update dummy1 set name = %s where id = %s")
    cur.execute(query, [threading.get_ident(), 8])
    print("before commit...", cur.rowcount)
    conn.commit()
    print("update to dummy1 done.")
    # 相手には見えない
    # 相手がselect for updateで別のレコードをselectしたら
    # この更新はそれとは別のレコードであるが、相手のトランザクションがコミットするまで
    # こちらは待機となった
    """
    """
    query = ("update dummy1 set name = %s where name = %s")
    cur.execute(query, [threading.get_ident(), "BBB"])
    rowcount = cur.rowcount
    conn.commit()
    print("update to dummy1 BBB done.", rowcount)
    # 相手には見えない
    # 相手がselect for updateしたら、そのコミットまでこちらは待機になる
    # 相手がコミットするということは相手の変更が反映されるので、
    # こちらの更新は空振りになる rowcount=0
    """

    print("t2 before select in t2...")
    sql = "select * from dummy1 where name = %s"
    cur.execute(sql, ["BBB"])
    print("t2 dummy1 select BBB 1回目", cur.fetchall())
    # 相手がselect for updateしていても通常のselectは通る
    # select for updateしているそのレコードでも待機しない

    """
    print("before select for update in t2...")
    sql = "select * from dummy1 where name = %s for update"
    cur.execute(sql, ["AAA"])
    print("dummy1 select for update AAA 1回目", cur.fetchall())
    # 相手のselect for updateしているテーブルは、
    # こちらのselect for updateが待機になる
    """

    print("t2 before update dummy2 CCC")
    query = ("update dummy2 set name = %s where name = %s")
    cur.execute(query, [threading.get_ident(), "CCC"])
    print("t2 before commit...", cur.rowcount)
    conn.commit()
    print("t2 update dummy2 CCC done.")
    # select for updateの対象ではないテーブルは操作可能

    """
    print("before select for update in t2...")
    sql = "select * from dummy2 where name = %s for update"
    cur.execute(sql, ["AAA"])
    print("dummy2 select for update AAA 1回目", cur.fetchall())
    # 相手のselect for updateしていないテーブルは、
    # こちらのselect for updateは実行される
    """

    print("t2 before update dummy1 CCC")
    query = ("update dummy1 set name = %s where name = %s")
    cur.execute(query, ["CCCc", "CCC"])
    print("t2 before commit...", cur.rowcount)
    conn.commit()
    print("t2 update dummy1 CCC done.")
    # テーブルの順番を間違うとデッドロックが発生する
    # select for updateされているテーブルは、それに関係ないレコードを操作しようとしても
    # 待機になる
    
    """
    print("before 1st update in t2...")
    query = ("update dummy2 set name = %s where name = %s")
    cur.execute(query, [threading.get_ident(), "AAA"])
    print("before commit...", cur.rowcount)
    conn.commit()
    print("update to dummy2 done.")
    # 相手のselect for updateとは別のテーブルの更新は通った
    # ただ、相手には見えない
    """

    """
    query = ("update dummy1 set name = %s where name = %s")
    cur.execute(query, ["BBB", "CCC"])
    rowcount = cur.rowcount
    conn.commit()
    print("update to dummy1 CCC done.", rowcount)
    # しかし相手がselect for updateしたテーブルへの更新は
    # 相手のトランザクションがコミットされるまで待機になった
    # こちらの更新対象が同じテーブルの全く関係ない別のレコードでも待機になる
    """
    """
    query = ("insert into dummy1(name, category_id)values(%s, %s)")
    cur.execute(query, ["BBB", 4])
    rowcount = cur.rowcount
    conn.commit()
    print("insert to dummy1 BBB done.", rowcount)
    # 相手のselect for updateのテーブルへのinsertは待機になった
    """
    """
    query = ("delete from dummy1 where name = %s")
    cur.execute(query, ["CCC"])
    rowcount = cur.rowcount
    conn.commit()
    print("delete dummy1 CCC done.", rowcount)
    # 相手に関係しないレコードのdeleteも待機
    """

t1 = threading.Thread(target=test1)
t2 = threading.Thread(target=test2)

t1.start()
t2.start()
