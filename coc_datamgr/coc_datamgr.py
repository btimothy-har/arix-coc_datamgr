from redbot.core import commands

class AriXCOC_DataMgr(commands.Cog):
    """AriX Clash of Clans Data Management"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def com1(self, ctx):
        """This does stuff!"""
        # Your code will go here
        await ctx.send("Hello world!")