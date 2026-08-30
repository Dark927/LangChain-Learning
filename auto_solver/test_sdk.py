import asyncio
from google.antigravity import Agent, LocalAgentConfig

async def main():
    config = LocalAgentConfig(system_instructions='reply only yes')
    async with Agent(config) as agent:
        r = await agent.chat('hello')
        print("AGENT REPLIED:", r.text)

if __name__ == '__main__':
    asyncio.run(main())
