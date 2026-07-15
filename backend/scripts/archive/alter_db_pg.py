import psycopg2

def main():
    conn = psycopg2.connect("dbname=crm_db user=postgres password=password host=localhost")
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE products ADD COLUMN image_url VARCHAR(255);")
        conn.commit()
        print("added image_url")
    except Exception as e:
        conn.rollback()
        print("err:", e)
    
    try:
        cur.execute("ALTER TABLE products ADD COLUMN specifications JSONB;")
        conn.commit()
        print("added specifications")
    except Exception as e:
        conn.rollback()
        print("err:", e)
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
