from redbot.core import Config, commands
from discord.utils import get

import discord

async def clash_embed(ctx, title=None, message=None, url=None, show_author=True, color=None):
    if not title:
        title = ""
    if not message:
        message = ""
    if color == "success":
        color = 0x00FF00
    elif color == "fail":
        color = 0xFF0000
    else:
        color = await ctx.embed_color()
    if url:
        embed = discord.Embed(title=title,url=url,description=message,color=color)
    else:
        embed = discord.Embed(title=title,description=message,color=color)
    if show_author:
        embed.set_author(name=f"{ctx.author.display_name}#{ctx.author.discriminator}",icon_url=ctx.author.avatar_url)
    #embed.set_footer(text="Ataraxy Clash of Clans",icon_url="https://i.imgur.com/xXjjWke.png")
    return embed

class AriXClashDataMgr(commands.Cog):
    """AriX Clash of Clans Data Management"""

    def __init__(self):
        self.config = Config.get_conf(self,identifier=2170311125702803,force_registration=True)
        default_global = {
            "datapath":"",
            "apikey":"",
            }
        default_guild = {
            "postlogs":False,
            "logchannel":0,
            }

        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)

    @commands.group(name="cdatapath",autohelp=False)
    @commands.is_owner()
    async def cdatapath(self, ctx):
        """Retrieves the data path location for Clash data files."""

        if not ctx.invoked_subcommand:
            async def no_path():
                embed = await clash_embed(ctx=ctx,message=f"Error encountered in retrieving the data path. There may be no data path currently set.",color="fail")
                return embed

            try:
                dataPath = await self.config.datapath()
            except:
                embed = await no_path()
                return await ctx.send(embed=embed)
            else:
                if dataPath == "":
                    embed = await no_path()
                    return await ctx.send(embed=embed)
                else:
                    embed = await clash_embed(ctx=ctx,message=f"The global data path is currently set to ```{dataPath}```.")
                    return await ctx.send(embed=embed)

    @cdatapath.command(name="set")
    @commands.is_owner()
    async def cdatapathset(self,ctx, path=""):
        """Sets the data path location."""
        try:
            newPath = path
            await self.config.datapath.set(newPath)
            
            setPath = await self.config.datapath()
            embed = await clash_embed(ctx=ctx,message=f"Global data path set to ```{setPath}```.",color="success")
            return await ctx.send(embed=embed)
        except:
            embed = await clash_embed(ctx=ctx,message=f"Error setting global data path.",color="fail")
            return await ctx.send(embed=embed)

    @commands.group(name="apikey",autohelp=False)
    @commands.is_owner()
    async def apikey(self, ctx):
        """Retrieves the current API Key for the Clash of Clans API."""

        if not ctx.invoked_subcommand:
            async def no_key():
                embed = await clash_embed(ctx=ctx,message=f"Error encountered in retrieving the API Key. There may be no API Key currently set.",color="fail")
                return embed

            try:
                apiKey = await self.config.apikey()
            except:
                embed = await no_key()
                return await ctx.send(embed=embed)
            else:
                if apiKey == "":
                    embed = await no_key()
                    return await ctx.send(embed=embed)
                else:
                    embed = await clash_embed(ctx=ctx,message=f"The API Key currently in use is ```{apiKey}```.")
                    return await ctx.send(embed=embed)

    @apikey.command(name="set")
    @commands.is_owner()
    async def apikeyset(self, ctx, key=""):
        """Sets the API Key for the Clash of Clans API."""

        try:
            newKey = key
            await self.config.apikey.set(newKey)
            
            setKey = await self.config.apikey()
            embed = await clash_embed(ctx=ctx,message=f"The API Key has been set to ```{setKey}```.",color="success")
            return await ctx.send(embed=embed)
        except:
            embed = await clash_embed(ctx=ctx,message=f"Error setting API Key.",color="fail")
            return await ctx.send(embed=embed)

    @commands.group(name="serverset",autohelp=False)
    @commands.admin_or_permissions(administrator=True)
    async def serversettings(self,ctx):
        """Configure settings for the current server."""

        if not ctx.invoked_subcommand:
            try:
                logsBool = await self.config.guild(ctx.guild).postlogs()
                logChannel = await self.config.guild(ctx.guild).logchannel()

                try:
                    channelObject = ctx.guild.get_channel(logChannel)
                    channelMention = f"<#{channelObject.id}>"
                except:
                    channelMention = "Invalid Channel"
                
            except:
                embed = await clash_embed(ctx=ctx,message=f"Error encountered in retrieving server settings.",color="fail")
                return await ctx.send(embed=embed)
            else:
                embed = await clash_embed(ctx=ctx,message=f"**Send Logs?:** {logsBool}\n**Log Channel:** {channelMention}")
                return await ctx.send(embed=embed)

    @serversettings.command(name="setlogs")
    @commands.admin_or_permissions(administrator=True)
    async def setlogs(self, ctx, boolset:bool):
        """Configure whether to send data logs in the current server."""

        try:
            newSetting = boolset
            await self.config.guild(ctx.guild).postlogs.set(newSetting)

            logsBool = await self.config.guild(ctx.guild).postlogs()
            logChannel = await self.config.guild(ctx.guild).logchannel()
            
            try:
                channelObject = ctx.guild.get_channel(logChannel)
                channelMention = f"<#{channelObject.id}>"
            except:
                channelMention = "Invalid Channel"

            embed = await clash_embed(ctx=ctx,title="Settings updated.",message=f"**Send Logs?:** {logsBool}\n**Log Channel: {channelMention}")
            return await ctx.send(embed=embed)
        except:
            embed = await clash_embed(ctx=ctx,message=f"Error updating settings.",color="fail")
            return await ctx.send(embed=embed)

    @serversettings.command(name="setchannel")
    @commands.admin_or_permissions(administrator=True)
    async def setchannel(self, ctx, channel:discord.TextChannel):
        """Configure channel to send log messages in."""

        try:
            await self.config.guild(ctx.guild).logchannel.set(channel.id)

            logsBool = await self.config.guild(ctx.guild).postlogs()
            logChannel = await self.config.guild(ctx.guild).logchannel()
            
            try:
                channelObject = ctx.guild.get_channel(logChannel)
                channelMention = f"<#{channelObject.id}>"
            except:
                channelMention = "Invalid Channel"

            embed = await clash_embed(ctx=ctx,title="Settings updated.",message=f"**Send Logs?:** {logsBool}\n**Log Channel: {channelMention}")
            return await ctx.send(embed=embed)
        except:
            embed = await clash_embed(ctx=ctx,message=f"Error updating settings.",color="fail")
            return await ctx.send(embed=embed)
