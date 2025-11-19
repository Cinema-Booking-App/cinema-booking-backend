import asyncio
import websockets

async def test_client(id):
    uri = "ws://localhost:8000/api/v1/ws/seats/7"
    async with websockets.connect(uri) as websocket:
        await websocket.send(f"Hello from client {id}")
        response = await websocket.recv()
        print(f"Client {id} nhận: {response}")

async def main():
    # Chạy song song 10 client
    await asyncio.gather(*[test_client(i) for i in range(10)])

if __name__ == "__main__":
    asyncio.run(main())
