import discord
import traceback
import asyncio
import pymongo

from typing import Union, Optional, Literal
from discord.ext import commands, tasks
from discord.commands import user_command, permissions
from formatting.constants import UNITS
from formatting.embed import gen_embed
from __main__ import log, db

class Pubcord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_boosters.start()

    def cog_unload(self):
        self.check_boosters.cancel()

    def has_modrole():
        async def predicate(ctx):
            document = await db.servers.find_one({"server_id": ctx.guild.id})
            if document['modrole']:
                role = discord.utils.find(lambda r: r.id == document['modrole'], ctx.guild.roles)
                return role in ctx.author.roles
            else:
                return False

        return commands.check(predicate)

    @user_command(guild_ids=[432379300684103699], name='Verify User', default_permission=False)
    @permissions.has_role("Moderator")
    async def verifyrank(self, ctx, member: discord.Member):
        if ctx.guild.get_role(432388746072293387) in ctx.author.roles:
            roles = member.roles
            verified_role = ctx.guild.get_role(719791739367325706)
            if verified_role not in roles:
                roles.append(verified_role)
                await member.edit(roles=roles)
                await ctx.respond(content='Verified user.', ephemeral=True)
            else:
                await ctx.respond(content='User already verified.', ephemeral=True)
        else:
            await ctx.respond(content='You do not have access to this command.', ephemeral=True)

    @tasks.loop(seconds=120)
    async def check_boosters(self):
        log.info('running pubcord booster role parity check')
        pubcord = self.bot.get_guild(432379300684103699)
        emoteserver = self.bot.get_guild(815821301700493323)
        pubcord_booster_role = pubcord.get_role(913239378598436966)
        for member in pubcord.premium_subscribers:
            if not member.get_role(913239378598436966):
                log.info('adding member to booster role - boosting main server')
                roles = member.roles
                roles.append(pubcord_booster_role)
                await member.edit(roles=roles, reason="Boosting main server")

        for member in emoteserver.premium_subscribers:
            pubcord_member = pubcord.get_member(member.id)
            if pubcord_member:
                if not pubcord_member.get_role(913239378598436966):
                    log.info('adding member to booster role - boosting emote server')
                    roles = pubcord_member.roles
                    roles.append(pubcord_booster_role)
                    await pubcord_member.edit(roles=roles, reason="Boosting emote server")

        for member in pubcord_booster_role.members:
            emoteserver_member = emoteserver.get_member(member.id)
            if emoteserver_member:
                if emoteserver_member not in emoteserver.premium_subscribers:
                    if member not in pubcord.premium_subscribers:
                        log.info('not boosting either server, removing')
                        roles = member.roles
                        roles.remove("role_id")
                        await member.edit(roles=roles, reason="No longer boosting main OR emote server")
        log.info('parity check complete')

    @check_boosters.before_loop
    async def wait_ready(self):
        # log.info('wait till ready')
        await self.bot.wait_until_ready()

    @commands.command(name='currentstatus',
                      description='Sends a embed with the latest status on EN Bandori.',
                      help='Usage\n\n%currentstatus')
    @commands.check_any(commands.has_guild_permissions(manage_messages=True), has_modrole())
    async def currentstatus(self, ctx, message_id: Optional[str]):
        embed = gen_embed(
            title='Current Status of EN Bandori',
            content='As updated from the official social media accounts, Google Play has been in contact they are already working on a solution. Expect confirmation soon this week before they can announce the rescheduled v4.10.0.'
        )
        embed.set_image(url='https://media.discordapp.net/attachments/432382183072858131/913234967067262976/IMG_6952.png?width=646&height=675')
        embed.add_field(name=f'What does this mean for us?',
                        value=f'The delay means that the scheduled collaboration will be postponed to 12/11-12/19 (subject to change). Subsequent events will follow in order after the collab, and the duration of events will not be shortened any further to compensate for the delay. The accelerated schedule will continue as planned.',
                        inline=False)
        embed.add_field(name=f'When will the update be done?',
                                value=f'There is **no ETA** at this time. Our community manager states that we should not "**expect any events in the next few (2-3) days**"',
                                inline=False)
        embed.set_footer(text='Last Updated 11/28/2021')
        if message_id:
            emessage = await ctx.channel.fetch_message(int(message_id))
            if emessage:
                await emessage.edit(embed=embed)

        qmember = ctx.guild.get_member(137977559546724352)
        qembed = gen_embed(
            name=qmember.name,
            icon_url=qmember.display_avatar.url,
            title='Quoted Message:',
            content='''Latest update:
                        - We're in discussions with Google and the facts of the case have been established, so we're working on resolution now.
                        - Still awaiting confirmation on what will be done, but don't expect any events in the next few (2-3) days either.'
                        ''')
        e2message = await ctx.channel.fetch_message(913960026920591380)
        await e2message.edit(embed=qembed)
        await ctx.message.delete()

def setup(bot):
    bot.add_cog(Pubcord(bot))