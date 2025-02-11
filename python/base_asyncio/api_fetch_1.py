import asyncio
import time

async def fetch_from_api(resource_id):
    await asyncio.sleep(2)
    print(f"Finished fetching from API at {time.strftime('%X')}")
    return 42

# Perform the fetch 3 times
async def main():
    coros = []
    for i in range(3):
        coro = fetch_from_api(i)
        coros.append(coro)
    response_values = await asyncio.gather(*coros) # gather returns a list
    return len(response_values)

print(f"Starting the main() method at {time.strftime('%X')}")
output = asyncio.run(main())
print(f"Ending the main() method at {time.strftime('%X')}. Output is {output}")