import httpx
import asyncio

async def main():
    url = "http://localhost:8000/crm/products/upload-image"
    files = {'file': ('test.png', b'dummy content', 'image/png')}
    # Since we need a token, we should get one first
    async with httpx.AsyncClient() as client:
        # Login
        login_data = {'username': 'vikas@example.com', 'password': 'Admin@123'}
        login_res = await client.post("http://localhost:8000/auth/login", data=login_data)
        token = login_res.json().get('access_token')
        
        headers = {'Authorization': f'Bearer {token}'}
        response = await client.post(url, headers=headers, files=files)
        print(response.status_code)
        print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
