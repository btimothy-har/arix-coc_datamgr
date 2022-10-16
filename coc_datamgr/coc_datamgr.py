import os
import sys

import discord
import coc

import json
import asyncio
import random
import time

from os import path
from dotenv import load_dotenv
from redbot.core import Config, commands
from discord.utils import get
from datetime import datetime
from string import ascii_letters, digits
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice

load_dotenv()

sys.path.append(os.getenv("RESOURCEPATH"))
from clash_resources import token_confirmation, standard_confirmation, react_confirmation, clashFileLock, datafile_retrieve, datafile_save, get_current_alliance, get_current_season, clash_embed, player_shortfield, player_embed, getPlayer
from clash_resources import ClashPlayerError

async def datafile_defaults():
    currSeason = await get_current_season()
    alliance = {'currentSeason': currSeason,
                'trackedSeasons': [],
                'clans':{},
                'members':{}
                }
    members = {}
    warlog = {}
    capitalraid = {}
    return alliance,members,warlog,capitalraid

class AriXClashDataMgr(commands.Cog):
    """AriX Clash of Clans Data Management"""

    def __init__(self):
        self.config = Config.get_conf(self,identifier=2170311125702803,force_registration=True)
        default_global = {
            "lastWarCheck":0
            }
        default_guild = {
            "postlogs":False,
            "logchannel":0,
            }
        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)

    async def cog_initialize(self):
        #Initializes API Login and Data Directory.
        coc_client = coc.EventsClient()
        
        try:
            await coc_client.login(os.getenv("CLASH_DEV_EMAIL"), os.getenv("CLASH_DEV_PASSWORD"))
        except coc.InvalidCredentials as error:
            await ctx.send("error")
        
        self.cDirPath = os.getenv("DATAPATH")
        self.cClient = coc_client

    @commands.group(name="datafiles",autohelp=False)
    @commands.is_owner()
    async def datafiles(self,ctx):
        """Checks if data files are present in the environment data path."""
        if not ctx.invoked_subcommand:
            embed = await clash_embed(ctx=ctx,
                                        title="Data File Status",
                                        message=f"**alliance.json**: {path.exists(self.cDirPath+'/alliance.json')}"
                                                +f"\n**members.json**: {path.exists(self.cDirPath+'/members.json')}"
                                                +f"\n**warlog.json**: {path.exists(self.cDirPath+'/warlog.json')}"
                                                +f"\n**capitalraid.json**: {path.exists(self.cDirPath+'/capitalraid.json')}"
                                                +f"\n\nRun `[p]datafiles init` to create any missing files.")
            await ctx.send(embed=embed)

    @datafiles.command(name="init")
    @commands.is_owner()
    async def datafiles_init(self, ctx):
        """Creates any missing data files."""

        currSeason = await get_current_season()
        default_alliance, default_members, default_warlog, default_capitalraid = await datafile_defaults()

        if not path.exists(self.cDirPath+'/alliance.json'):
            await datafile_save(self,'alliance',default_alliance)

        if not path.exists(self.cDirPath+'/members.json'):
            await datafile_save(self,'members',default_members)

        if not path.exists(self.cDirPath+'/warlog.json'):
            await datafile_save(self,'warlog',default_warlog)

        if not path.exists(self.cDirPath+'/capitalraid.json'):
            await datafile_save(self,'capitalraid',default_capitalraid)
        
        embed = await clash_embed(ctx=ctx,
                                title="Data Files Initialized.",
                                message=f"**alliance.json**: {path.exists(self.cDirPath+'/alliance.json')}"
                                        +f"\n**members.json**: {path.exists(self.cDirPath+'/members.json')}"
                                        +f"\n**warlog.json**: {path.exists(self.cDirPath+'/warlog.json')}"
                                        +f"\n**capitalraid.json**: {path.exists(self.cDirPath+'/capitalraid.json')}",
                                color="success")
        await ctx.send(embed=embed)

    @datafiles.command(name="reset")
    @commands.is_owner()
    async def datafiles_reset(self, ctx):
        """Erases all current data and resets all data files."""

        embed = await clash_embed(ctx=ctx,
                                title="Confirmation Required.",
                                message=f"**This action erases __ALL__ data from the bot.**"+
                                        "\n\nIf you wish to continue, enter the token below as your next message.")
        await ctx.send(content=ctx.author.mention,embed=embed)

        if not await token_confirmation(self,ctx):
            return
        
        currSeason = await get_current_season()
        default_alliance, default_members, default_warlog, default_capitalraid = await datafile_defaults()
            
        await datafile_save(self,'alliance',default_alliance)
        await datafile_save(self,'members',default_members)
        await datafile_save(self,'warlog',default_warlog)
        await datafile_save(self,'capitalraid',default_capitalraid)
            
        embed = await clash_embed(ctx=ctx,
                    title="All Data Files Reset.",
                    message=f"**alliance.json**: {path.exists(self.cDirPath+'/alliance.json')}"
                            +f"\n**members.json**: {path.exists(self.cDirPath+'/members.json')}"
                            +f"\n**warlog.json**: {path.exists(self.cDirPath+'/warlog.json')}"
                            +f"\n**capitalraid.json**: {path.exists(self.cDirPath+'/capitalraid.json')}",
                    color="success")
            
        await ctx.send(embed=embed)

    @commands.group(name="serverset",autohelp=False)
    @commands.admin_or_permissions(administrator=True)
    async def serversettings(self,ctx):
        """Configure settings for the current server."""
        if not ctx.invoked_subcommand:

            if ctx.channel.type == discord.ChannelType.private:
                embed = await clash_embed(ctx=ctx,message=f"This command cannot be used in DMs.",color="fail")
                return await ctx.send(embed=embed)

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
                embed = await clash_embed(ctx=ctx,
                                    title=f"Settings for {ctx.guild.name}",
                                    message=f"**Send Logs?:** {logsBool}\n**Log Channel:** {channelMention}",
                                    thumbnail=ctx.guild.icon_url)
                return await ctx.send(embed=embed)

    @serversettings.command(name="setlogs")
    @commands.admin_or_permissions(administrator=True)
    async def setlogs(self, ctx, boolset:bool):
        """Configure whether to send data logs in the current server."""

        if ctx.channel.type == discord.ChannelType.private:
            embed = await clash_embed(ctx=ctx,message=f"This command cannot be used in DMs.",color="fail")
            return await ctx.send(embed=embed)

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

            embed = await clash_embed(ctx=ctx,title="Settings updated.",message=f"**Send Logs?:** {logsBool}\n**Log Channel:** {channelMention}", color="success")
            return await ctx.send(embed=embed)
        except:
            embed = await clash_embed(ctx=ctx,message=f"Error updating settings.",color="fail")
            return await ctx.send(embed=embed)

    @serversettings.command(name="setchannel")
    @commands.admin_or_permissions(administrator=True)
    async def setchannel(self, ctx, channel:discord.TextChannel):
        """Configure channel to send log messages in."""

        if ctx.channel.type == discord.ChannelType.private:
            embed = await clash_embed(ctx=ctx,message=f"This command cannot be used in DMs.",color="fail")
            return await ctx.send(embed=embed)

        try:
            await self.config.guild(ctx.guild).logchannel.set(channel.id)

            logsBool = await self.config.guild(ctx.guild).postlogs()
            logChannel = await self.config.guild(ctx.guild).logchannel()
            
            try:
                channelObject = ctx.guild.get_channel(logChannel)
                channelMention = f"<#{channelObject.id}>"
            except:
                channelMention = "Invalid Channel"

            embed = await clash_embed(ctx=ctx,title="Settings updated.",message=f"**Send Logs?:** {logsBool}\n**Log Channel:** {channelMention}",color="success")
            return await ctx.send(embed=embed)
        except:
            embed = await clash_embed(ctx=ctx,message=f"Error updating settings.",color="fail")
            return await ctx.send(embed=embed)

    @commands.group(name="clanset",autohelp=False)
    @commands.admin_or_permissions(administrator=True)
    async def clansettings(self,ctx):
        """Add/Remove Clans from the Data Manager."""
            
        if not ctx.invoked_subcommand:
            currentClans,currentMembers = await get_current_alliance(self)
            await ctx.send(f"Clan Set:{currentClans}")

    @clansettings.command(name="add")
    @commands.admin_or_permissions(administrator=True)
    async def clansettings_add(self, ctx, tag:str, abbr:str):
        """Add a clan to the Data Manager."""
        if not coc.utils.is_valid_tag(tag):
            embed = await clash_embed(ctx=ctx,
                            message=f"Invalid tag, please double check your entry and try again."
                                    +f"\n\nYou provided: `{tag}`",
                            color="fail")

            return await ctx.send(embed=embed)

        try:
            clan = await self.cClient.get_clan(tag)
        except coc.NotFound:
            embed = await clash_embed(ctx=ctx,
                            message=f"Could not find this Clan. Please check and try again."
                                    +f"\n\nYou provided: `{tag}`",
                            color="fail")
            return await ctx.send(embed=embed)

        embed = await clash_embed(ctx=ctx,
                            message=f"Please confirm that you would like to add the below clan.\nTo confirm, enter the token below as your next message.",
                            thumbnail=clan.badge.url)

        embed.add_field(name=f"**{clan.name} ({clan.tag})**",
                        value=f"Level: {clan.level}\u3000\u3000Location: {clan.location} / {clan.chat_language}"+
                            f"\n```{clan.description}```",
                        inline=False)

        await ctx.send(embed=embed)

        if not await token_confirmation(self,ctx):
            return

        allianceJson = await datafile_retrieve(self,'alliance')
        warlogJson = await datafile_retrieve(self,'warlog')
        capitalraidJson = await datafile_retrieve(self,'capitalraid')

        allianceJson['clans'][clan.tag] = {
            'name':clan.name,
            'abbr':abbr,
            }
        warlogJson[clan.tag] = {}
        capitalraidJson[clan.tag] = {}

        await datafile_save(self,'alliance',allianceJson)
        await datafile_save(self,'warlog',warlogJson)
        await datafile_save(self,'capitalraid',capitalraidJson)

        await ctx.send(f"Successfully added **{clan.tag} {clan.name}**!")

    @clansettings.command(name="remove")
    @commands.admin_or_permissions(administrator=True)
    async def clansettings_remove(self, ctx, tag:str):
        """Remove a clan from the Data Manager."""

        currentClans,currentMembers = await get_current_alliance(self)
        tag = coc.utils.correct_tag(tag)

        if not coc.utils.is_valid_tag(tag):
            embed = await clash_embed(ctx=ctx,
                            message=f"Invalid tag, please double check your entry and try again."
                                    +f"\n\nYou provided: `{tag}`",
                            color="fail")
            return await ctx.send(embed=embed)

        if tag not in clansList:
            embed = await clash_embed(ctx=ctx,
                            message=f"This Clan isn't registered with the Alliance."
                                    +f"\n\nYou provided: `{tag}`",
                            color="fail")
            return await ctx.send(embed=embed)

        try:
            clan = await self.cClient.get_clan(tag)
        except coc.NotFound:
            embed = await clash_embed(ctx=ctx,
                            message=f"Could not find this Clan. Please check and try again."
                                    +f"\n\nYou provided: `{tag}`",
                            color="fail")
            return await ctx.send(embed=embed)

        embed = await clash_embed(ctx=ctx,
                            message=f"Please confirm that you would like to remove the below clan.\nTo confirm, enter the token below as your next message.",
                            thumbnail=clan.badge.url)

        embed.add_field(name=f"**{clan.name} ({clan.tag})**",
                        value=f"Level: {clan.level}\u3000\u3000Location: {clan.location} / {clan.chat_language}"+
                            f"\n```{clan.description}```",
                        inline=False)

        await ctx.send(embed=embed)

        if not await token_confirmation(self,ctx):
            return

        allianceJson = await datafile_retrieve(self,'alliance')

        del allianceJson['clans'][clan.tag]

        await datafile_save(self,'alliance',allianceJson)

        await ctx.send(f"Successfully removed **{clan.tag} {clan.name}**!")

    @commands.group(name="member",autohelp=False)
    @commands.admin_or_permissions(administrator=True)
    async def membermanage(self,ctx):
        """Member Management Tasks."""
        
        if not ctx.invoked_subcommand:
            pass

    @membermanage.command(name="add")
    @commands.admin_or_permissions(administrator=True)
    async def membermanage_add(self,ctx,user:discord.User, clan_abbreviation:str, *tags):
        """Add members to the Alliance. Multiple tags can be separated by a blank space."""

        homeClan = None
    
        processAdd = []
        successAdd = []
        failedAdd = []

        allianceJson = await datafile_retrieve(self,'alliance')
        memberStatsJson = await datafile_retrieve(self,'members')

        currentClans = list(allianceJson['clans'].keys())
        currentMembers = list(allianceJson['members'].keys())

        if not len(currentClans) >= 1:
            return await ctx.send("No clans registered to the Alliance! Please first register a clan with `[p]clanset add`.")

        if len(tags) == 0:
            return await ctx.send("Provide Player Tags to be added. Separate multiple tags with a space.")

        try:
            userID = user.id
        except:
            return await ctx.send("Unable to retrieve Discord User ID.")

        for clanTag in currentClans:
            if allianceJson['clans'][clanTag]['abbr'] == clan_abbreviation:
                try:
                    clan = await self.cClient.get_clan(clanTag)
                except:
                    pass
                else:
                    homeClan = clan

        if not homeClan:
            return await ctx.send(f"The Clan abbreviation **{clan_abbreviation}** does not correspond to any registered clan.")

        cEmbed = await clash_embed(ctx,
            title=f"Please confirm that you are adding the below accounts.",
            message=f"Discord User: {user.mention}"
                    + f"\nHome Clan: {homeClan.tag} {homeClan.name}")

        for tag in tags:
            tag = coc.utils.correct_tag(tag)

            try:
                p = await getPlayer(self,ctx,tag,force_member=True)
            except ClashPlayerError as err:
                p = None
                errD = {
                    'tag':tag,
                    'reason':'Unable to find a user with this tag.'
                    }
                failedAdd.append(errD)
                continue
            except:
                p = None
                errD = {
                    'tag':tag,
                    'reason':'Unknown error.'
                    }
                failedAdd.append(errD)
                continue
            
            fTitle, fStr = await player_shortfield(self,ctx,p)
            cEmbed.add_field(
                name=f"**{fTitle}**",
                value=f"{fStr}",
                inline=False)
            processAdd.append(p)

        if len(processAdd) > 0:
            cMsg = await ctx.send(embed=cEmbed)
            if not await react_confirmation(self,ctx,cMsg):
                return

            for p in processAdd:
                p.newMember(userID,homeClan.tag)
                pAllianceJson,pMemberJson = p.toJson()
                    
                allianceJson['members'][p.player.tag] = pAllianceJson
                memberStatsJson[p.player.tag] = pMemberJson
                successAdd.append(
                    {
                    'player':p,
                    'clan':homeClan
                    }
                )
            await datafile_save(self,'alliance',allianceJson)
            await datafile_save(self,'members',memberStatsJson)

        successStr = "\u200b"
        failStr = "\u200b"
        for success in successAdd:
            successStr += f"**{success['player'].player.tag} {success['player'].player.name}** added to {success['clan'].tag} {success['clan'].name}.\n"

        for fail in failedAdd:
            failStr += f"{fail['tag']}: {fail['reason']}\n"

        aEmbed = await clash_embed(ctx=ctx,title=f"Operation Report: New Member(s)")

        aEmbed.add_field(name=f"**__Success__**",
                        value=successStr,
                        inline=False)
        aEmbed.add_field(name=f"**__Failed__**",
                        value=failStr,
                        inline=False)

        return await ctx.send(embed=aEmbed)

    @membermanage.command(name="remove")
    @commands.admin_or_permissions(administrator=True)
    async def membermanage_remove(self,ctx,*tags):
        """Remove members from the Alliance. Multiple tags can be separated by a blank space."""

        processRemove = []
        successRemove = []
        failedRemove = []

        allianceJson = await datafile_retrieve(self,'alliance')

        currentClans = list(allianceJson['clans'].keys())
        currentMembers = list(allianceJson['members'].keys())

        cEmbed = await clash_embed(ctx,
            title=f"I found the below accounts to be removed. Please confirm this action.")

        for tag in tags:
            tag = coc.utils.correct_tag(tag)

            if tag not in currentMembers:
                errD = {
                    'tag':tag,
                    'reason':'Could not find this tag in the member list.'
                    }
                failedRemove.append(tag)
                continue

            if allianceJson['members'][tag]['is_member'] == False:
                errD = {
                    'tag':tag,
                    'reason':'Not currently an active member.'
                    }
                failedRemove.append(tag)
                continue

            try:
                p = await getPlayer(self,ctx,tag,force_member=True)
            except ClashPlayerError as err:
                p = None
                errD = {
                    'tag':tag,
                    'reason':'Unable to find a user with this tag.'
                    }
                failedRemove.append(errD)
                continue
            except:
                p = None
                errD = {
                    'tag':tag,
                    'reason':'Unknown error.'
                    }
                failedRemove.append(errD)
                continue

            fTitle, fStr = await player_shortfield(self,ctx,p)
            cEmbed.add_field(
                name=f"**{fTitle}**",
                value=f"\n{fStr}"
                    +f"Home Clan: {p.memberStatus} of {allianceJson['clans'][p.homeClan]['name']}"
                    + f"\nLinked To: <@{p.discordUser}>",
                inline=False)
            processRemove.append(p)

        if len(processRemove) > 0:
            cMsg = await ctx.send(embed=cEmbed)
            if not await react_confirmation(self,ctx,cMsg):
                return

            for p in processRemove:
                p.removeMember()
                pAllianceJson,pMemberJson = p.toJson()
                    
                allianceJson['members'][p.player.tag] = pAllianceJson
                successRemove.append(
                    {
                    'player':p,
                    }
                )
            await datafile_save(self,'alliance',allianceJson)

        successStr = "\u200b"
        failStr = "\u200b"
        for success in successRemove:
            successStr += f"**{success['player'].tag} {success['player'].name}** removed from {allianceJson['clans'][success['player'].homeClan]['name']}.\n"

        for fail in failedRemove:
            failStr += f"{fail['tag']}: {fail['reason']}\n"

        aEmbed = await clash_embed(ctx=ctx,title=f"Operation Report: Remove Member(s)")

        aEmbed.add_field(name=f"**__Success__**",
                        value=successStr,
                        inline=False)

        aEmbed.add_field(name=f"**__Failed__**",
                        value=failStr,
                        inline=False)
        return await ctx.send(embed=aEmbed)

    @membermanage.command(name="promote")
    @commands.admin_or_permissions(administrator=True)
    async def membermanage_promote(self,ctx,user:discord.User):
        """Promote all of a User's Accounts in the specified clan."""

        #successRemove = []
        #failedRemove = []

        #userTags = []
        #userClans = []

        #try:
        #    userID = user.id
        #except:
        #    return await ctx.send("Unable to retrieve Discord User ID.")

        #allianceJson = await datafile_retrieve(self,'alliance')

        #for tag, member in allianceJson['members'].items(): 
        #    if member['discord_user'] == userID:
        #        userTags.append(tag)
        #        userClans.append(member['home_clan'])

        #if len(userTags==0) or len(userClans==0):
        #    return await ctx.send("This user has no registered accounts or clans.")
        #elif len(userClans) == 1:
        #    promoteClan = userClan[0]
        #else:
        #    pass

        #userAccountStr = ""

        #for tag in userTags:
        #    p = await getPlayer(self,ctx,tag,force_member=True)
        #    userAccounts.append(p)

    @commands.command(name="drefresh")
    async def data_update(self, ctx):

        sendLogs = False
        newSeason = False

        try:
            logsBool = await self.config.guild(ctx.guild).postlogs()
            sendLogs = logsBool
        except:
            pass

        try:
            logChannel = await self.config.guild(ctx.guild).logchannel()
        except:
            pass
        else:
            try:
                logChannelO = ctx.guild.get_channel(logChannel)
            except:
                sendLogs = False
                logChannelO = None

        successLog = []
        errLog = []
        t = time.time()

        season = await get_current_season()
        allianceJson = await datafile_retrieve(self,'alliance')
        memberStatsJson = await datafile_retrieve(self,'members')
        warlogJson = await datafile_retrieve(self,'warlog')
        capitalraidJson = await datafile_retrieve(self,'capitalraid')

        sEmbed = await clash_embed(ctx,
                title="Data Update Status Report",
                show_author=False)

        if str(season) != str(allianceJson['currentSeason']):
            newSeason = True
            nSeason = season
            pSeason = allianceJson['currentSeason']
            allianceJson['trackedSeasons'] = []
            allianceJson['trackedSeasons'].append(pSeason)

            os.makedirs(self.cDirPath+'/'+pSeason)
            with open(self.cDirPath+'/'+pSeason+'/members.json','x') as file:
                json.dump(memberStatsJson,file,indent=2)
            with open(self.cDirPath+'/'+pSeason+'/warlog.json','x') as file:
                json.dump(warlogJson,file,indent=2)
            with open(self.cDirPath+'/'+pSeason+'/capitalraid.json','x') as file:
                json.dump(capitalraidJson,file,indent=2)

            default_alliance, default_members, default_warlog, default_capitalraid = await datafile_defaults()
            memberStatsJson = default_members
            warlogJson = default_warlog
            capitalraidJson = default_capitalraid

            await datafile_save(self,'members',default_members)
            await datafile_save(self,'warlog',default_warlog)
            await datafile_save(self,'capitalraid',default_capitalraid)

            sEmbed.add_field(
                name=f"**New Season Initialized: {nSeason}**",
                value=f"__Files Saved__"
                    + f"\n**{pSeason}/members.json**: {path.exists(self.cDirPath+'/'+pSeason+'/members.json')}"
                    + f"\n**{pSeason}/warlog.json**: {path.exists(self.cDirPath+'/'+pSeason+'/warlog.json')}"
                    + f"\n**{pSeason}/capitalraid.json**: {path.exists(self.cDirPath+'/'+pSeason+'/capitalraid.json')}"
                    + f"\n\u200b\n"
                    + f"__Files Created__"
                    + f"\n**members.json**: {path.exists(self.cDirPath+'/members.json')}"
                    + f"\n**warlog.json**: {path.exists(self.cDirPath+'/warlog.json')}"
                    + f"\n**capitalraid.json**: {path.exists(self.cDirPath+'/capitalraid.json')}",
                inline=False)

        for tag, member in allianceJson['members'].items():
            try:
                p = await getPlayer(self,ctx,tag,force_member=True)
            except ClashPlayerError as err:
                p = None
                errD = {
                    'tag':tag,
                    'reason':'Unable to find a user with this tag.'
                    }
                errLog.append(errD)
                continue
            except:
                p = None
                errD = {
                    'tag':tag,
                    'reason':'Unknown error.'
                    }
                errLog.append(errD)
                continue

            p.updateStats()
            aJson, mJson = p.toJson()

            memberStatsJson[tag] = mJson
            successLog.append(p)

        await datafile_save(self,'members',memberStatsJson)

        errStr = "\n"
        for e in errLog:
            errStr += f"{e['tag']}: {e['reason']}\n"

        sEmbed.add_field(
            name=f"**Member Updates Completed",
            value=f"{len(successLog)} records updated. {len(errLog)} errors encountered."+errStr,
            inline=False)
        
        if sendLogs:
            await logChannelO.send(embed=sEmbed)