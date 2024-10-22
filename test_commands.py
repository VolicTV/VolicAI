import asyncio
from bot import Bot
from twitchio.ext import commands

class MockWebsocket:
    async def send(self, message):
        print(f"Mock websocket sent: {message}")

class MockChannel:
    def __init__(self, name):
        self.name = name
        self._ws = MockWebsocket()

    async def send(self, content):
        print(f"Mock channel {self.name} sent: {content}")

class MockUser:
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self._ws = MockWebsocket()

class MockContext:
    def __init__(self, author_name, channel_name):
        self.author = MockUser(author_name, '12345')
        self.channel = MockChannel(channel_name)
        self.message = MockMessage(f"!command from {author_name}", self.author, self.channel)

class MockMessage:
    def __init__(self, content, author, channel):
        self.content = content
        self.author = author
        self.channel = channel
        self.echo = False
        self.tags = {}
        self._ws = MockWebsocket()

async def test_commands(bot):
    ctx = MockContext('test_user', 'test_channel')
    
    # List of commands to test
    command_tests = [
        ('quote', []),
        ('quotesearch', ['valorant']),
        ('quotecount', []),
        ('lastquote', []),
        ('airesponse', ['Tell me a joke']),
        ('roast', ['@someuser']),
        ('compatibility', ['@user1', '@user2']),
        # Add more commands here
    ]

    for command_name, args in command_tests:
        print(f"\nTesting command: !{command_name}")
        command = bot.get_command(command_name)
        if command:
            try:
                ctx.message.content = f"!{command_name} {' '.join(args)}"
                await bot.handle_commands(ctx.message)
                print(f"Command !{command_name} executed successfully")
            except Exception as e:
                print(f"Error executing !{command_name}: {str(e)}")
        else:
            print(f"Command !{command_name} not found")

    # Test event_message
    message = MockMessage('Hello, bot!', ctx.author, ctx.channel)
    await bot.event_message(message)
    print("\nTested event_message")

async def main():
    bot = Bot()
    await bot.connect()  # This initializes the bot without actually connecting to Twitch
    await test_commands(bot)
    await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
