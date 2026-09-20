import discord
from discord.ext import commands
import yt_dlp
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# Menggunakan prefix kc! sesuai permintaan
bot = commands.Bot(command_prefix='kc!', intents=intents)

# Dictionary untuk menyimpan antrean lagu tiap server
queues = {}

ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

@bot.event
async def on_ready():
    print(f'Bot {bot.user} siap memutar musik dengan sistem antrean!')

@bot.command()
async def halo(ctx):
    await ctx.send(f'Halo juga, {ctx.author.mention}! Saya Kuroo bot.')

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await channel.connect()
            await ctx.send(f"Berhasil bergabung ke channel: {channel.name}")
        else:
            await ctx.voice_client.move_to(channel)
    else:
        await ctx.send("Masuk ke voice channel dulu ya!")

# Fungsi untuk memutar lagu berikutnya dari antrean
def play_next(ctx):
    guild_id = ctx.guild.id
    if guild_id in queues and len(queues[guild_id]) > 0:
        next_url, next_title = queues[guild_id].pop(0)
        source = discord.FFmpegPCMAudio(next_url, **ffmpeg_options)
        ctx.voice_client.play(source, after=lambda e: play_next(ctx))
        # Menggunakan asyncio untuk mengirim pesan ke chat
        asyncio.run_coroutine_threadsafe(ctx.send(f'🎵 Sekarang memutar dari antrean: **{next_title}**'), bot.loop)

@bot.command(name='play')
async def play(ctx, *, search: str):
    if not ctx.author.voice:
        await ctx.send("Anda harus masuk ke voice channel terlebih dahulu!")
        return

    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await channel.connect()

    async with ctx.typing():
        try:
            data = ytdl.extract_info(search, download=False)
            if 'entries' in data:
                data = data['entries'][0]
            
            url = data['url']
            title = data['title']
            
            guild_id = ctx.guild.id

            # Jika bot sedang memutar lagu, masukkan ke antrean
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                if guild_id not in queues:
                    queues[guild_id] = []
                queues[guild_id].append((url, title))
                await ctx.send(🛡️ f'Ditambahkan ke antrean: **{title}**')
            else:
                # Jika tidak ada lagu yang diputar, langsung putar
                source = discord.FFmpegPCMAudio(url, **ffmpeg_options)
                ctx.voice_client.play(source, after=lambda e: play_next(ctx))
                await ctx.send(f'🎵 Sedang memutar: **{title}**')
        except Exception as e:
            await ctx.send(f"Terjadi kesalahan saat memutar lagu: {e}")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Lagu dilewati!")
    else:
        await ctx.send("Tidak ada lagu yang sedang diputar.")

@bot.command()
async def leave(ctx):
    guild_id = ctx.guild.id
    if guild_id in queues:
        queues[guild_id].clear()
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Bot keluar dari voice channel dan antrean dibersihkan.")
    else:
        await ctx.send("Bot sedang tidak berada di voice channel.")

bot.run('MASUKKAN_TOKEN_BOT_ANDA_DISINI')