import asyncio
import discord
import re

from discord.ext import commands
from discord.commands import user_command
from formatting.embed import gen_embed
from typing import Union, Optional
from formatting.embed import embed_splitter
from __main__ import log, db

class Tiering(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def convert_room(argument):
        if re.search('^\d{5}$', argument):
            return argument
        elif re.search('^\w+',argument):
            log.warning('Bad Argument - Room Code')
            raise discord.ext.commands.BadArgument(message="This is not a valid room code.")
        else:
            return None

    def convert_spot(argument):
        if re.search('^\d{5}$', argument):
            log.warning('Bad Argument - Room Code')
            raise discord.ext.commands.BadArgument()
        elif re.search('^\d{1}$', argument):
            return argument
        elif re.search('^[Ff]$', argument):
            return "0"
        else:
            log.warning('Bad Argument - Room Code')
            raise discord.ext.commands.BadArgument(message="This is not a valid option. Open spots must be a single digit number.")

    def has_modrole():
        async def predicate(ctx):
            document = await db.servers.find_one({"server_id": ctx.guild.id})
            if document['modrole']:
                role = discord.utils.find(lambda r: r.id == document['modrole'], ctx.guild.roles)
                return role in ctx.author.roles
            else:
                return False
        return commands.check(predicate)

    @user_command(name = 'Add user to filler list')
    async def addfiller(self, ctx, member: discord.Member):
        document = await db.fillers.find_one({'server_id': ctx.guild.id})
        log.info('found document')
        if document:
            fillers = document['fillers']
        else:
            fillers = []
        if member.id in fillers:
            await ctx.respond(content = 'User is already in the list of fillers.', ephemeral=True)
        else:
            fillers.append(member.id)
            log.info('appended')
            await db.fillers.update_one({'server_id': ctx.guild.id}, {"$set": {"fillers": fillers}}, upsert=True)
            log.info('updated one')
            await ctx.respond(content = f"Added {member.name} to the list of fillers.", ephemeral=True)

    @commands.group(name='trackfiller',
                    description='Manage the filler tracking feature for the server.')
    async def trackfiller(self, ctx):
        await ctx.send(embed = gen_embed(title='Before you use Kanon to track fillers', content= 'You or the server moderators will need to reauthorize Kanon to use application commands. You can do so by visiting the following link:\nhttps://s-neon.xyz/kanon'))
        pass

    @trackfiller.command(name='list',
                         aliases=['get'],
                         description='Show the list of all the fillers.')
    async def list(self, ctx):
        fillers = []
        document = await db.fillers.find_one({'server_id': ctx.guild.id})
        for memberid in document['fillers']:
            member = await self.bot.fetch_user(memberid)
            fillers.append(member.name)
        fillers_str = ", ".join(fillers)
        embed = gen_embed(title='List of Fillers',
                          content=f'{fillers_str}')
        await embed_splitter(embed = embed, destination = ctx.channel)

    @trackfiller.command(name='clear',
                         description='Clear the list of all names.')
    async def clear(self, ctx):
        await db.fillers.update_one({'server_id': ctx.guild.id}, {"$set": {"fillers": []}})
        await ctx.send(embed = gen_embed(title='Track Fillers - Clear', content = 'List of fillers has been cleared.'))

    @trackfiller.command(name='remove',
                         aliases=['delete'],
                         description='Remove one or more users from the list.',
                         help='Usage:\n\n%trackfiller remove [user mentions/user ids/user name + discriminator (ex: name#0000)]')
    async def remove(self, ctx, members: commands.Greedy[discord.Member]):
        document = await db.fillers.find_one({'server_id': ctx.guild.id})
        fillers = document['fillers']
        for member in members:
            fillers.remove(member.id)

    @commands.command(name = 'efficiencyguide',
                      description = 'Generates an efficiency guide for tiering in the channel you specify.',
                      help = 'Example:\n\n%efficiencyguide #tiering-etiquette')
    @commands.check_any(commands.has_guild_permissions(manage_messages=True), has_modrole())
    async def efficiencyguide(self, ctx, channel: discord.TextChannel):
        embed = gen_embed(
                    name = f"{ctx.guild.name}",
                    icon_url = ctx.guild.icon.url,
                    title = 'Tiering Etiqeutte and Efficiency',
                    content = 'Efficiency guidelines taken from LH 2.0, originally made by Binh and edited by doom_chicken.'
                    )
        embed.set_image(url = 'https://files.s-neon.xyz/share/bandori-efficiency.png')
        await channel.send(embed=embed)
        embed = gen_embed(
                    title = 'Menuing',
                    content = 'Spam the bottom right of your screen in between songs. See video for an example:'
                    )
        embed.set_footer(text=discord.Embed.Empty)
        await channel.send(embed=embed)
        await channel.send(content='https://twitter.com/Binh_gbp/status/1106789316607410176')
        embed = gen_embed(
                    title='Swaps',
                    content="Try to have someone ready to swap with you by the time you're done. Ping the appropriate roles (usually standby, or t100 or even t1000) and when you're planning to stop.  Say \"scores\" in your room's chat channel when you finish the song and \"open\" when you're out of the room.  Ideally whoever is swapping in should be spamming the room code to join as soon as they see \"scores.\" If possible, being in VC with the tierers can greatly smooth out this process."
                    )
        embed.set_footer(text=discord.Embed.Empty)
        await channel.send(embed=embed)
        embed = gen_embed(
                    title='Pins/Frames/Titles',
                    content='Pins/Frames/Titles - Please remove any and all existing pins as well as setting the default frame; these will slow down the room greatly with additional loading times. I would also prefer if you went down to one title before you join any rooms, but no need to leave if forgotten.'
                )
        embed.set_footer(text=discord.Embed.Empty)
        await channel.send(embed=embed)
        embed = gen_embed(
                    title='Flame Sync',
                    content='Flame syncing will now operate with the remake of the room every set of 90 🔥. If multiple sets are being done, a room maker should be designated. The flame check setting should now be turned OFF from now on.'
                )
        embed.set_footer(text=discord.Embed.Empty)
        await channel.send(embed=embed)
        embed = gen_embed(
                    title='Skip Full Combo',
                    content="Break combo somewhere in the song, it'll skip the FC animation and save a few seconds."
                )
        embed.set_footer(text=discord.Embed.Empty)
        await channel.send(embed=embed)
        embed = gen_embed(
                    title='Rooming Guidelines',
                    content="**Starting with 3-4 people** can potentially be better than dealing with the chance of bad pubs depending on the event.\n\nFor extremely competitive events, iOS and high end Android devices are given priority."
                )
        embed.set_footer(text=discord.Embed.Empty)
        await channel.send(embed=embed)
        await ctx.send(embed=gen_embed(title='efficiencyguide', content=f'Tiering etiquette and efficiency guide posted in {channel.mention}'))

    @commands.command(name='vsliveguide',
                      description='Generates a versus live guide for tiering in the channel you specify. This includes gift box and lazy doormat info.',
                      help='Example:\n\n%vsliveguide #tiering-etiquette')
    @commands.check_any(commands.has_guild_permissions(manage_messages=True), has_modrole())
    async def vsliveguide(self, ctx, channel: discord.TextChannel):
        embed = gen_embed(
            name=f"{ctx.guild.name}",
            icon_url=ctx.guild.icon.url,
            title='Versus Live Tiering Info',
            content='Graciously stolen from **Zia** & **Blur** and the **Play Act! Challenge*Audition** server, edited by **Neon**'
        )
        embed.set_footer(text=discord.Embed.Empty)
        await channel.send(embed=embed)
        embed = gen_embed(
            title="Marina's Gift Box Can Efficiency",
            content="""This chart helps you get the most boost cans as efficiently as possible.
            It lets you know whether you should keep opening gifts from a box or move on to the next box (if possible) based on the probability of pulling a boost can.
            \nTo use this chart, make sure turn on the settings called
            \n"Exchange All" & "Stop on Special Prize".
            \nOnce you have collected the special prize, you can look at this chart to determine if you should keep pulling or move to the next box."""
        )
        embed.set_image(url='https://files.s-neon.xyz/share/marina_box.png')
        embed.add_field(
            name='Green',
            value='Favourable probability - **continue opening**'

        )
        embed.add_field(
            name='Red',
            value='Unfavourable probability - **skip to next box**'

        )
        embed.add_field(
            name='White',
            value='Neutral probability - **keep opening OR skip to next box**'

        )
        embed.set_footer(text=discord.Embed.Empty)
        await channel.send(embed=embed)
        embed = gen_embed(
            title="Lazy Doormat Strategy",
            content='Follow the chart below to obtain the best efficiency.'
        )
        embed.add_field(
            name='Songs',
            value="```\nUnite! From A to Z: 87 / 124 / 252 / 357/ 311 (SP)\nJumpin': 63 / 102 / 185 / 281\nKizuna Music: 78 / 127 / 207 / 265\nFuwa Fuwa Time: 52 / 98 / 192 / 272\nB.O.F - 54 / 88 / 207 / 306\nLegendary EN: 64 / 100 / 189 / 272\nHome Street: 65 / 111 / 193 / 269\nStraight Through Our Dreams!: 52 / 107 / 184 / 280\nInitial: 86 / 114 / 218 / 341\nKorekara: 59 / 104 / 170 / 296\nKyu~Mai * Flower: 73 / 108 / 226 / 351```"
        )
        embed.set_footer(text=discord.Embed.Empty)
        await channel.send(embed=embed)
        await ctx.send(embed=gen_embed(title='vsliveguide',
                                       content=f'Versus Live guide posted in {channel.mention}'))

    @commands.command(name='room',
                      aliases=['rm'],
                      description='Changes the room name without having to go through the menu. If no arguments are provided, the room will be changed to a dead room. Rooms must start with the standard tiering prefix "g#-".\nBoth parameters are optional.',
                      help='Usage:\n\n%room <open spots> <room number>\n\nExample:\n\n`%room 1 12345`\nFor just changing room number - `%room 12345`\nFor just changing open spots - `%room 3`')
    @commands.cooldown(rate=2,per=600.00,type=commands.BucketType.channel)
    async def room(self, ctx, open_spots: Optional[convert_spot], room_num: Union[convert_room, None]):
        currentname = ctx.channel.name
        namesuffix = ""
        if re.search('^g\d-', currentname):
            nameprefix=re.match("^g\d-", currentname).group(0)
        else:
            log.warning('Error: Invalid Channel')
            await ctx.send(embed=gen_embed(title='Invalid Channel',
                                           content=f'This is not a valid tiering channel. Please match the format g#-xxxxx to use this command.'))
            return
        if re.search('-[\df]$', currentname):
            namesuffix=re.search("-[\df]$", currentname).group(0)

        if room_num:
            if open_spots:
                open_spots = int(open_spots)
                if 0 < open_spots <= 4:
                    namesuffix=f'-{open_spots}'
                elif open_spots == 0:
                    namesuffix='-f'
                else:
                    log.warning('Error: Invalid Input')
                    await ctx.send(embed=gen_embed(title='Input Error',
                                                   content=f'That is not a valid option for this parameter. Open spots must be a value from 0-4.'))
                    return

            await ctx.channel.edit(name=f'{nameprefix}{room_num}{namesuffix}')
            await ctx.send(embed=gen_embed(title='room',
                                           content=f'Changed room code to {room_num}'))
        else:
            if open_spots:
                open_spots = int(open_spots)
                if 0 < open_spots <= 4:
                    namesuffix=f'-{open_spots}'
                    nameprefix=re.search("(^g\d-.+)(?![^-])(?<!-[\df]$)",currentname).group(0)
                elif open_spots == 0:
                    namesuffix='-f'
                    nameprefix = re.search("(^g\d-.+)(?![^-])(?<!-[\df]$)", currentname).group(0)
                else:
                    log.warning('Error: Invalid Input')
                    await ctx.send(embed=gen_embed(title='Input Error',
                                                   content=f'That is not a valid option for this parameter. Open spots must be a value from 0-4.'))
                    return
                await ctx.channel.edit(name=f'{nameprefix}{namesuffix}')
                await ctx.send(embed=gen_embed(title='room',
                                               content=f'Changed open spots to {open_spots}'))
            else:
                await ctx.channel.edit(name=f'{nameprefix}xxxxx')
                await ctx.send(embed=gen_embed(title='room',
                                               content=f'Closed room'))

    #async def connect(self, ctx, label, dest_server):


def setup(bot):
    bot.add_cog(Tiering(bot))