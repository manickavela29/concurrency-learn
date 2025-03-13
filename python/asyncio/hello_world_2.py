import asyncio

async def async_function():
    await asyncio.sleep(2)
    print("Slept for 2 seconds")
    
coro =  async_function()

asyncio.run(coro)

# If async_function doesn't have await statement, 
# then it will be executed synchronously without sleeping for 2 seconds
