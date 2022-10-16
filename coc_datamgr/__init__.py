import os
import discord
import coc

from redbot.core.bot import Red
from .coc_datamgr import AriXClashDataMgr

async def setup(bot:Red):
    cog = AriXClashDataMgr()
    await cog.cog_initialize()
    bot.add_cog(cog)