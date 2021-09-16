import asyncio
import math
import discord
import eyed3
import os
import youtube_dl
import validators
from discord.ext import commands, tasks
from dotenv import load_dotenv
from tinydb import TinyDB, Query
from tinydb.operations import increment
from discordTogether import DiscordTogether
from youtubesearchpython import VideosSearch


class Soundboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_soundlist()

    load_dotenv()
    soundDir = []
    soundDict = {}
    path_to_soundfiles = str(os.getenv('SOUNDFILE_PATH'))

    def update_soundlist(self):
        """Updates the soundlist variables"""
        for file in sorted(os.listdir(self.path_to_soundfiles)):
            if file.__contains__('mp3'):
                self.soundDict[file] = eyed3.load(self.path_to_soundfiles + '/' + file).tag.artist
                self.soundDir.append(file)

    @staticmethod
    def check(author):
        """Check if message author is the same author."""

        def inner_check(message):
            if message.author != author:
                return False
            return True

        return inner_check

    @staticmethod
    def print_table(data, cols, wide):
        """Prints formatted data on columns of given width."""
        n, r = divmod(len(data), cols)
        pat = '{{:{}}}'.format(wide)
        line = '\n'.join(pat * cols for _ in range(n))
        return line.format(*data)

    @staticmethod
    def search_soundlist(search, sounddict):
        """Searcher through dict.values and gets all the items containing search."""
        clean_soundlist = [x.lower().strip('.mp3') for x in list(sounddict.keys())]
        results = []
        for sound in clean_soundlist:
            if search in sound:
                results.append(clean_soundlist.index(sound))
        return results

    def create_soundboardlist(self, sound_dict):
        """Creates string that shows all the avaible sounds"""
        sb_list_messages = []
        tables = []
        float_sep = math.modf(len(sound_dict) / 30)
        keys_list = list(sound_dict)
        for amount_table in range(round(float_sep[1]) + 1):
            temptable = []
            lefttable = []
            if len(sound_dict) >= 20:
                for x in range(20):
                    if (30 * amount_table + x + 20) >= len(sound_dict):
                        lefttable.append(str('[' + str(30 * amount_table + x + 1) + '] ' + list(sound_dict.keys())[
                            30 * amount_table + x].strip('.mp3') + ' by: ' + sound_dict[
                                                 list(sound_dict.keys())[30 * amount_table + x]]))
                        continue
                    temptable.append(str(
                        '[' + str(30 * amount_table + x + 1) + '] ' + list(sound_dict.keys())[
                            30 * amount_table + x].strip('.mp3') + ' by: ' +
                        sound_dict[list(sound_dict.keys())[30 * amount_table + x]]))
                    temptable.append(str('[' + str(30 * amount_table + x + 21) + '] ' + list(sound_dict.keys())[
                        30 * amount_table + x + 20].strip('.mp3') + ' by: ' + sound_dict[
                                             list(sound_dict.keys())[30 * amount_table + x + 20]]))
                tables.append(temptable)
            else:
                for x in range(len(sound_dict)):
                    if (30 * amount_table + x + 20) >= len(sound_dict):
                        lefttable.append(str('[' + str(30 * amount_table + x + 1) + '] ' + list(sound_dict.keys())[
                            30 * amount_table + x].strip('.mp3') + ' by: ' + sound_dict[
                                                 list(sound_dict.keys())[30 * amount_table + x]]))
                        continue
                    temptable.append(str(
                        '[' + str(30 * amount_table + x + 1) + '] ' + list(sound_dict.keys())[
                            30 * amount_table + x].strip('.mp3') + ' by: ' +
                        sound_dict[list(sound_dict.keys())[30 * amount_table + x]]))
                    temptable.append(str('[' + str(30 * amount_table + x + 21) + '] ' + list(sound_dict.keys())[
                        30 * amount_table + x + 20].strip('.mp3') + ' by: ' + sound_dict[
                                             list(sound_dict.keys())[30 * amount_table + x + 20]]))
                tables.append(temptable)

        strlefttable = "\n"
        for table in lefttable:
            strlefttable += table + '\n'
        for table in tables:
            if table is tables[-1]:
                sb_list_messages.append("```ini\n" + self.print_table(table, 2, 43) + strlefttable + "\n```")
            else:
                sb_list_messages.append("```ini\n" + self.print_table(table, 2, 43) + "\n```")
        return sb_list_messages

    def create_search_soundlist(self, searchresults, sounddict):
        """Creates a list to show the search results."""
        search_soundDict = {}
        for result in searchresults:
            search_soundDict[list(sounddict.keys())[result].strip('.mp3')] = sounddict[list(sounddict.keys())[result]]
        return self.create_soundboardlist(search_soundDict), search_soundDict

    async def get_response(self, ctx, sounddict):
        try:
            msg = await self.bot.wait_for('message', check=self.check(ctx.author), timeout=25)
        except asyncio.TimeoutError:
            await ctx.send('You took to long :sleeping:')
            return
        if str(msg.content) == "cancel":
            return False
        msgnumber = int(msg.content)
        if msgnumber - 1 > len(sounddict):
            await ctx.send('Number not in the list please try again')
            return await self.get_response(ctx, sounddict)
        return msgnumber

    @commands.command(name='sblist')
    async def soundboardlist(self, ctx):
        """Shows all sounds that are available and if you type a number it will the the associate sound."""
        for sb_messages in self.create_soundboardlist(self.soundDict):
            await ctx.send(sb_messages)
        await ctx.send("Type a number to make a choice or type cancel to stop")
        response = await self.get_response(ctx, self.soundDict)
        if not response:
            return
        try:
            await self.soundboard(ctx, self.soundDir[response - 1].strip('.mp3'))
        except AttributeError:
            await ctx.send("You are currently not in a voice channel!\nPlease join a voice channel.")
        await ctx.message.delete()

    @commands.command(name='sbsearch')
    async def soundboardsearch(self, ctx, search):
        """Search trough all the available sounds and show them, then type a number to play the sound."""
        results = self.search_soundlist(search.lower(), self.soundDict)
        if results:
            css = self.create_search_soundlist(results, self.soundDict)
            for result_list in css[0]:
                await ctx.send(result_list)
            await ctx.message.delete()
            await ctx.send("Type a number to make a choice or type cancel to stop")
            response = await self.get_response(ctx, css[1])
            if not response:
                return
            try:
                await self.soundboard(ctx, self.soundDir[results[response - 1]].strip('.mp3'))
            except AttributeError:
                await ctx.send("You are currently not in a voice channel!\nPlease join a voice channel.")
        else:
            await ctx.send("Could not find any sounds matching that description")

    @commands.command(name="sb")
    async def soundboard(self, ctx, sound):
        """Play the sound given in parameter, this can be the name or index in list."""
        vc = ctx.voice_client
        if sound.isdigit():
            vc.play(discord.FFmpegOpusAudio(source=self.path_to_soundfiles + '/' + self.soundDir[int(sound) - 1]))
        else:
            vc.play(discord.FFmpegOpusAudio(source=self.path_to_soundfiles + '/' + sound + ".mp3"))
        await ctx.message.delete()

    @commands.command(name="reload")
    async def reload(self, ctx):
        """Reloads the soundboard."""
        self.update_soundlist()
        await ctx.message.channel.send(
            "All sounds are reloaded!"
        )
        await ctx.message.delete()

    @soundboard.before_invoke
    @soundboardsearch.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ytdl_format_options = {
        'format': 'bestaudio/best',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
    }
    ffmpeg_options = {
        'options': '-vn',
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
    }
    ytdl = youtube_dl.YoutubeDL(ytdl_format_options,)
    song_queue = []
    player_queue = []

    def play_next(self, ctx):
        if len(self.player_queue) >= 1:
            self.player_queue.pop(0)
            self.song_queue.pop(0)
            try:
                ctx.voice_client.play(self.player_queue[0], after=lambda e: self.play_next(ctx))
            except IndexError:
                return
        else:
            return

    async def from_url(self, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=not stream))
        filename = data['url'] if stream else self.ytdl.prepare_filename(data)
        self.song_queue.append(data['title'])
        return discord.FFmpegPCMAudio(filename, **self.ffmpeg_options)

    @commands.command(name="p")
    async def p(self, ctx, *, url):
        """Streams from a url"""
        return await self.play(ctx, url=url)

    @commands.command(name="removesong")
    async def remove_song(self, ctx, index: int):
        """Remove song from playlist at index"""
        await ctx.send("🎶 Removed: " + self.song_queue[index - 1] + " from the queue")
        self.song_queue.pop(index - 1)
        self.player_queue.pop(index - 1)

    @commands.command(name="playlist")
    async def playlist(self, ctx):
        """Lists the current playlist"""
        if len(self.song_queue) >= 1:
            playlist_string = "```ini\n"
            for x, y in enumerate(self.song_queue):
                playlist_string += '[' + str(x + 1) + ']' + " " + str(y) + '\n'

            playlist_string += "```"
            await ctx.send(playlist_string)
        else:
            await ctx.send("🎶 Playlist is empty you an add song by using the command !p <url> or !play <url>")

    @commands.command(name="play")
    async def play(self, ctx, *, url):
        """Streams from a url"""
        vc = ctx.voice_client
        if not validators.url(url):
            search_result = VideosSearch(url, limit=1)
            url = search_result.result()['result'][0]['link']

        if vc.is_playing():
            self.player_queue.append(await self.from_url(url))
            await ctx.send("🎶 Added: " + self.song_queue[-1] + " to the playlist")
            return

        player = await self.from_url(url, loop=bot.loop, stream=True)
        self.player_queue.append(player)
        ctx.voice_client.play(player, after=lambda e: self.play_next(ctx))
        await ctx.send("🎶 Now Playing: " + self.song_queue[-1])

    @commands.command(name="skip")
    async def skip(self, ctx):
        """Skips the current song"""
        ctx.voice_client.stop()

    @commands.command(name="stop")
    async def stop(self, ctx):
        """Stops the player"""
        self.song_queue.clear()
        self.player_queue.clear()
        ctx.voice_client.stop()

    @p.before_invoke
    @play.before_invoke
    @skip.before_invoke
    @stop.before_invoke
    @remove_song.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


class Streepje(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists(self.path_to_database):
            open(self.path_to_database, 'w+')

    load_dotenv()
    path_to_database = str(os.getenv('STREEPJES_DB'))
    db = TinyDB(path_to_database)
    User = Query()
    streepjes_messages = {}

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.emoji == "👍":
            if reaction.message.id in self.streepjes_messages.keys():
                if user.id == self.streepjes_messages[reaction.message.id][1]:
                    await reaction.remove(user)
                elif reaction.count == 3:
                    if reaction.message.id in self.streepjes_messages.keys():
                        if not self.db.search(self.User.name == self.streepjes_messages[reaction.message.id][0]):
                            self.db.insert({'name': self.streepjes_messages[reaction.message.id][0], 'streepjes': 1})
                        else:
                            self.db.update(increment('streepjes'),
                                           self.User.name == self.streepjes_messages[reaction.message.id][0])
                        await reaction.message.channel.send(
                            "{} now has {} streepje(s)".format(
                                bot.get_user(self.streepjes_messages[reaction.message.id][0]).name, self.db.search(
                                    self.User.name == self.streepjes_messages[reaction.message.id][0])[0]['streepjes']))

    @commands.command(name="streepjeslist")
    async def streepjeslist(self, ctx):
        """Shows the current standing of streepjes."""
        message = ""
        for person in self.db.all():
            message += "{person} : {streepjes}\n".format(person=self.bot.get_user(person['name']).name,
                                                         streepjes=person['streepjes'])
        if message == "":
            await ctx.message.channel.send("There aren't any streepjes in the database.")
        else:
            await ctx.message.channel.send(message)
        await ctx.message.delete()

    @commands.command(name="streepje")
    async def streepje(self, ctx, person):
        """Gives streepjes to a user."""
        if ctx.message.author.permissions_in(ctx.message.channel).ban_members:
            if not self.db.search(self.User.name == ctx.message.mentions[0].id):
                self.db.insert({'name': ctx.message.mentions[0].id, 'streepjes': 1})
            else:
                self.db.update(increment('streepjes'), self.User.name == ctx.message.mentions[0].id)
            await ctx.message.channel.send(
                "{Person} now has {streepjes} streepje(s)".format(Person=ctx.message.mentions[0].name,
                                                                  streepjes=str(self.db.search(
                                                                      self.User.name == int(
                                                                          ctx.message.mentions[0].id))[0][
                                                                                    'streepjes'])))
        else:
            await ctx.message.channel.send(
                "{Author} wants to add a streepje to {Person}.\n3 👍 are needed!".format(
                    Author=ctx.message.author.mention, Person=person))
            messages = await ctx.message.channel.history(limit=10).flatten()
            await messages[0].add_reaction(emoji='👍')
            self.streepjes_messages[messages[0].id] = [ctx.message.mentions[0].id, ctx.message.author.id]


class Jeopardy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    teams = []
    buzer = False

    @commands.command(name="mkteam")
    async def make_team(self, ctx, personone, persontwo, teamname, soundid):
        """make team for Jeopardy."""
        if ctx.message.author.permissions_in(ctx.message.channel).ban_members:
            await ctx.send(
                "{personone} and {persontwo} are now team: {teamname} with soundID: {soundid}.".format(
                    personone=ctx.message.mentions[0].name,
                    persontwo=ctx.message.mentions[1].name, teamname=str(teamname), soundid=str(soundid)))
            self.teams.append([ctx.message.mentions[0].id, ctx.message.mentions[1].id, teamname, soundid])
        else:
            await ctx.send("Only admins are allowed to create teams.")

    @commands.command(name="reset")
    async def reset_question(self, ctx):
        """Reset question for Jeopardy."""
        if ctx.message.author.permissions_in(ctx.message.channel).ban_members:
            self.buzer = False
            await ctx.send("Buzzers are reset!")
        else:
            await ctx.send("Only admins are allowed to reset the question teams.")

    @commands.command(name="clrteams")
    async def clear_team(self, ctx):
        """clears teams for Jeopardy."""
        await ctx.send("Cleared all Jeopardy teams.")
        self.teams.clear()

    @commands.command(name="listteams")
    async def list_team(self, ctx):
        """lists all the teams for Jeopardy."""
        allteams = ""
        if allteams:
            for team in self.teams:
                allteams += "Team : " + team[2] + " with members: " + self.bot.get_user(
                    team[0]).name + " and " + self.bot.get_user(
                    team[1]).name + " with buzzer sound: " + team[3] + '\n'
            await ctx.send(allteams)
        else:
            await ctx.send("There aren't any teams, please make some teams.")

    @commands.command(name="buz")
    async def call(self, ctx):
        """Buzzez in for Jeopardy."""

        if self.teams:
            if self.buzer:
                await ctx.send("Buzzers are disabled waiting for reset!")
                return
            for team in self.teams:
                if ctx.message.author.id in team:
                    await ctx.send(team[2] + " Buzzed in!")
                    self.buzer = True
                    await Soundboard.soundboard(Soundboard(self.bot), ctx=ctx, sound=team[3])
                    return
            await ctx.send(
                ctx.message.author.name + " is not in a team!")
            return
        else:
            await ctx.send("There aren't any teams, please make some teams.")

    @call.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


class Together(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.togetherControl = DiscordTogether(bot)

    @commands.command('together')
    async def together(self, ctx, type):
        """Together: youtube, poker, chess, betrayal, fishing"""
        link = await self.togetherControl.create_link(ctx.author.voice.channel.id, str(type))
        await ctx.send(f"Click the blue link!\n{link}")

    @together.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents,
                   description="What's The Flight Plan Bot granted by Tacojesus.")


@bot.event
async def on_ready():
    print('Logged in as {0} ({0.id})'.format(bot.user))
    print('------')


@tasks.loop(seconds=60)
async def background_is_playing():
    if bot.voice_clients:
        for vc in bot.voice_clients:
            if not vc.is_playing():
                await vc.disconnect()


@bot.command()
async def join(ctx):
    """Join your current voicechannel."""
    channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.message.delete()


@bot.command()
async def leave(ctx):
    """Disconnect from current voicechannel."""
    await ctx.voice_client.disconnect()
    await ctx.message.delete()


@background_is_playing.before_loop
async def before_my_task():
    await bot.wait_until_ready()  # wait until the bot logs in


bot.add_cog(Soundboard(bot))
bot.add_cog(Music(bot))
bot.add_cog(Streepje(bot))
bot.add_cog(Jeopardy(bot))
bot.add_cog(Together(bot))

bot.run(TOKEN)
