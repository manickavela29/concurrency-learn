import asyncio

# Async function definition
async def async_function():
    print("Hello")
    
# Corroutine object is created , but not executed
coro =  async_function()

print("World")

# Performs actual function call of the coroutine
asyncio.run(coro)