import discord
from discord.ext import commands
import yt_dlp
import os
import asyncio
import validators
import json

intents = discord.Intents.all()
intents.members = True # enable the members intent
intents.presences = True

confile = open('config.json','r')
config = json.loads(confile.read())
confile.close()

bot = commands.Bot(command_prefix=config["prefix"], intents=intents, help_command=None, activity = discord.Game('!help', status = discord.Status.online))

#FFMPEG_OPTIONS = '-filter:a "atempo=2" -vn "bass=g=10:f=110:w=0.6" -ss 00:01:00 -filter:a "bass=g=15:f=110:w=0.6" -vn'
FFMPEG_OPTIONS = ''
FFMPEG_OPTIONS_BEFORE = ''


link = None
queue = []
cur_play = ""
reply_msg_play = None
reply_msg = None
queue_rpl = []
playlist = []
info_playlist = None
is_first_playlist = False
last_id = 0
is_playlist = False

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Список моих команд", color=0x00ff00)
    embed.add_field(name="!play <ссылка>", value="Воспроизводит аудио по ссылке", inline=False)
    embed.add_field(name="!skip <ссылка>", value="Воспроизводит следующее аудио из очереди", inline=False)
    embed.add_field(name="!pause", value="Ставит аудио на паузу", inline=False)
    embed.add_field(name="!resume", value="Продолжает воспроизведение аудио", inline=False)
    embed.add_field(name="!stop", value="Останавливает аудио и выходит из голосового канала", inline=False)
    embed.add_field(name="Сервисы поддерживаемых аудио", value="Soundcloud.com, Deezer.com, Youtube.com", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f"Бот {bot.user} готов к работе!")


async def create_queue(ctx, info):
    for entry in info["entries"]:
        print(entry["webpage_url"])
        await playload(ctx, entry["webpage_url"])
    await playerfun(ctx, False, True)
        


async def playload(ctx, url):
    global reply_msg_play
    global reply_msg
    global playlist
    global queue
    ydl_opts = {'format': 'm4a/bestaudio/best',
                'postprocessors': [{ 'key': 'FFmpegExtractAudio','preferredcodec': 'm4a'}]}
                #'paths': "D:/MAIRU MUSIC BOT/music",
                #'outtmpl': 'D:/MAIRU MUSIC BOT/music/music.m4a' }
   
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        #print(info)
        queue.append(info)  # добавляем новый URL в конец очереди

async def playerfun(ctx, is_skip, zaglushka):
    global link
    global reply_msg_play
    global reply_msg
    global playlist
    global cur_play
    global info_playlist
    global is_first_playlist
    global last_id
    global is_playlist
    channel = ctx.author.voice.channel
    if not bot.voice_clients:
        voice_client = await channel.connect()
    else: 
        voice_client = bot.voice_clients[0]
    if voice_client:
        if is_skip:
            voice_client.stop()
        if voice_client.is_playing():
            if not is_playlist:
                queue_rpl.append(await ctx.send(embed=discord.Embed(title = f'Трек {queue[len(queue)-1]["title"]} добавлен в очередь.', colour = discord.Color.blue())))               
        else:
            print("STARRRRRRRRRRRRRRRRRRRRRRRRRRRT")
            cur_play = queue.pop(0)
            try:
                unitaz = cur_play["uploader_url"].split('?')
            except:
                unitaz = ["deezer"]
            #print(cur_play)
            if 'youtu' in unitaz[0]:
                #print(cur_play["formats"][4]["fragments"][0]["url"] + '?fifo_size=1000000&overrun_nonfatal=1')
                source = discord.FFmpegPCMAudio(cur_play["formats"][4]["url"] + '?fifo_size=1000000&overrun_nonfatal=1',options=FFMPEG_OPTIONS,before_options=FFMPEG_OPTIONS_BEFORE)
            elif 'deezer' in unitaz[0]:
                source = discord.FFmpegPCMAudio(cur_play["url"],options=FFMPEG_OPTIONS,before_options=FFMPEG_OPTIONS_BEFORE)
            else:
                source = discord.FFmpegPCMAudio(cur_play["formats"][0]["url"],options=FFMPEG_OPTIONS,before_options=FFMPEG_OPTIONS_BEFORE)
            voice_client.play(source)
            user = bot.user
            emb = discord.Embed(title = f'Сейчас играет: {cur_play["title"]}', colour = discord.Color.blue())
            emb.set_author(name = bot.user.name, icon_url = bot.application.icon)
            emb.set_image(url = f'{cur_play["thumbnail"]}')
            if reply_msg_play:
                await reply_msg_play.delete()
            reply_msg_play = await ctx.send(
                embed = emb
            )
            if info_playlist:
                if is_playlist:
                    if last_id < info_playlist[0]["n_entries"]:
                        await playload(ctx, info_playlist[last_id+1]["webpage_url"])
                        last_id += 1
            while True:
                # ждем окончания воспроизведения текущего трека
                if not bot.voice_clients:
                    voice_client = await channel.connect()
                else: 
                    voice_client = bot.voice_clients[0]
                while voice_client.is_playing() or voice_client.is_paused():
                    await asyncio.sleep(2)

             # если очередь не пуста, берем следующий трек и воспроизводим его
                if len(queue) > 0:
                    print("STARRRRRRRRRRRRRRRRRRRRRRRRRRRT")
                    cur_play = queue.pop(0)
                    unitaz = "deezer"
                    try:
                        unitaz = cur_play["uploader_url"].split('?')
                    except:
                        unitaz = ["deezer"]
                    #print(cur_play)
                    if 'youtu' in unitaz[0]:
                        source = discord.FFmpegPCMAudio(cur_play["formats"][4]["url"] + '?fifo_size=1000000&overrun_nonfatal=1',options=FFMPEG_OPTIONS,before_options=FFMPEG_OPTIONS_BEFORE)
                    elif 'deezer' in unitaz[0]:
                        source = discord.FFmpegPCMAudio(cur_play["url"],options=FFMPEG_OPTIONS,before_options=FFMPEG_OPTIONS_BEFORE)
                    else:
                        source = discord.FFmpegPCMAudio(cur_play["formats"][0]["url"],options=FFMPEG_OPTIONS,before_options=FFMPEG_OPTIONS_BEFORE)
                    for i in range(1000000):
                        source.read()
                    voice_client.play(source)
                    user = bot.user
                    emb = discord.Embed(title = f'Сейчас играет: {cur_play["title"]}', colour = discord.Color.blue())
                    emb.set_author(name = bot.user.name, icon_url = bot.application.icon)
                    emb.set_image(url = f'{cur_play["thumbnail"]}')
                    if reply_msg_play:
                        await reply_msg_play.delete()
                    reply_msg_play = await ctx.send(
                        embed = emb
                    )
                    if is_playlist:
                        if last_id < info_playlist[0]["n_entries"]:
                            await playload(ctx, info_playlist[last_id+1]["webpage_url"])
                            last_id += 1
                # если очередь пуста, выходим из цикла
                else:
                    if reply_msg_play:
                        await reply_msg_play.delete()
                    if reply_msg: 
                        await reply_msg.delete()
                    for q_rpl in queue_rpl:
                        await q_rpl.delete()
                    #await reply_msg_play.delete()
                    await voice_client.disconnect()
                    break
            

@bot.command()
async def play(ctx, *, search):
    global link
    global reply_msg_play
    global reply_msg
    global playlist
    global info_playlist
    global is_first_playlist
    global is_playlist
    global last_id
    unitaz = search.split('?')
    if validators.url(search):
        channel = ctx.author.voice.channel
        last_id = 0
        if not channel:
            reply_msg = await ctx.send(embed=discord.Embed(title = "Вы не подключены к голосовому каналу.", colour = discord.Color.blue()))
            return
        if "/sets/" in unitaz[0]:
            if not bot.voice_clients: 
                is_playlist = True
                ydl_opts = {'format': 'm4a/bestaudio/best', 'postprocessors': [{ 'key': 'FFmpegExtractAudio','preferredcodec': 'm4a'}]}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(search, download=False)
                    info_playlist = info["entries"]
                    is_first_playlist = True
                    queue.append(info_playlist[0])
                    await playerfun(ctx, True, False)
                # await create_queue(ctx, info)
            else:
                ydl_opts = {'format': 'm4a/bestaudio/best', 'postprocessors': [{ 'key': 'FFmpegExtractAudio','preferredcodec': 'm4a'}]}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(search, download=False)
                await create_queue(ctx, info)
        else: 
            info_playlist = None
            is_playlist = False
            await playload(ctx, search)
            await playerfun(ctx, False, False)
        #await bot.connect()
            await ctx.message.delete()  # delete the user's message

    else:
        await ctx.send(embed=discord.Embed(title="Вы ввели некорректную ссылку."))
        await asyncio.sleep(15)
        if reply_msg: 
            await reply_msg.delete()

@bot.command()
async def skip(ctx):
    global reply_msg
    global reply_msg_play
    global cur_play
    global search_global
    global last_id
    voice_client = ctx.voice_client
    if voice_client.is_playing():
        voice_client.stop()
        if len(queue) > 0:
            await playerfun(ctx, True, False)
            await ctx.message.delete()
            for q_rpl in queue_rpl:
                await q_rpl.delete()
        else:
            reply_msg = await ctx.send(embed=discord.Embed(title="Очередь пуста.", colour = discord.Color.blue()))
            await reply_msg.delete()
            await ctx.message.delete()
    else:
        reply_msg = await ctx.send(embed=discord.Embed(title="Ничего не играет в данный момент.", colour = discord.Color.blue()))
    await asyncio.sleep(10)
    if ctx.message:
        await ctx.message.delete()  # delete the user's message
        
@bot.command()
async def pause(ctx):
    global reply_msg
    voice_client = ctx.voice_client
    if voice_client.is_playing():
        voice_client.pause()
        reply_msg = await ctx.send(embed=discord.Embed(title="Музыка поставлена на паузу.", colour = discord.Color.blue()))
    else:
        reply_msg = await ctx.send(embed=discord.Embed(title="В данный момент ничего не играет.", colour = discord.Color.blue()))
    await asyncio.sleep(10)
    if reply_msg:
        await reply_msg.delete()
    if ctx.message:
        await ctx.message.delete() # delete the user's message

@bot.command()
async def resume(ctx):
    global reply_msg
    voice_client = ctx.voice_client
    if voice_client.is_paused():
        voice_client.resume()
        reply_msg = await ctx.send(embed=discord.Embed(title="Музыка возобновлена.", colour = discord.Color.blue()))
    else:
        reply_msg = await ctx.send(embed=discord.Embed(title="Музыка не на паузе.", colour = discord.Color.blue()))
    await asyncio.sleep(10)
    if reply_msg:
        await reply_msg.delete()
    if ctx.message:
        await ctx.message.delete() # delete the user's message

@bot.command()
async def stop(ctx):
    global reply_msg_play
    voice_client = ctx.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
        reply_msg = await ctx.send(embed=discord.Embed(title="Отключился от голосового канала.", colour = discord.Color.blue()))
    else:
        reply_msg = await ctx.send(embed=discord.Embed(title="Я не подключен к голосовому каналу.", colour = discord.Color.blue()))
    await asyncio.sleep(10)
    if reply_msg:
        await reply_msg.delete()
    if ctx.message:
        await ctx.message.delete()  # delete the user's message
    # for q_rpl in queue_rpl:
    #     await q_rpl.delete()

bot.run(config["token"])