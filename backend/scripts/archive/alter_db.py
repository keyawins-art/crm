import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(user="postgres", password="password", database="crm_db", host="localhost")
    try:
        await conn.execute("ALTER TABLE products ADD COLUMN image_url VARCHAR(255);")
        print("Added image_url")
    except Exception as e:
        print(f"Error image_url: {e}")
        
    try:
        await conn.execute("ALTER TABLE products ADD COLUMN specifications JSONB;")
        print("Added specifications")
    except Exception as e:
        print(f"Error specifications: {e}")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
