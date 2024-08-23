import discord
from discord.ext import commands
import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio
from pytube import YouTube, Search
import youtube_dl
# Este es mi primer bot de Discord, cualquier sugerencia o algo por el estilo estoy abierto a que me las escriban, Twitter @Yaeko_Dev
# This is my first discord bot, any suggestions or anything like that I'm open to you writing them to me, Twitter @Yaeko_Dev

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

puntos = {}

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name}')
    await bot.tree.sync()

@bot.tree.command(name="play", description="Play a song in the voice channel")
@discord.app_commands.describe(song="Song name or YouTube link")
async def play_song(interaction: discord.Interaction, song: str):
    voice_channel = interaction.user.voice.channel
    if not voice_channel:
        await interaction.response.send_message("Debes estar en un canal de voz para reproducir música.", ephemeral=True)
        return

    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if not voice_client:
        voice_client = await voice_channel.connect()
    else:
        await voice_client.move_to(voice_channel)

    await interaction.response.send_message(f"Bot conectado al canal de voz: {voice_channel}", ephemeral=True)

    try:
        if "youtube.com" in song:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'pcm_s16le',
                    'preferredquality': '192',
                }],
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(song, download=False)
                audio_url = info['url']
        else:
            search = Search(query=song)
            results = search.results
            if not results:
                await interaction.followup.send("No se encontró ninguna canción con ese nombre.")
                await voice_client.disconnect()
                return
            video = results[0]
            audio_url = video.streams.get_audio_only().url

        voice_client.play(discord.FFmpegPCMAudio(audio_url))

        while voice_client.is_playing():
            await asyncio.sleep(1)

    except Exception as e:
        await interaction.followup.send(f"Error al reproducir la canción: {e}")
    finally:
        await voice_client.disconnect()

@bot.tree.command(name="trivia", description="Start a trivia game")
@discord.app_commands.describe(categoria="Category of the trivia")
async def trivia(interaction: discord.Interaction, categoria: str):
    categorias = {
        'vocaloid': '75bdwCGMigMnKsoat6V826',
        'jpop': '2jwRBCVEewMzG68ur3qds6',
        'kpop': '2EoheVFjqIxgJMb8VnDRtZ',
        'pop': '37i9dQZF1EQncLwOalG3K7',
        'reggaeton': '07iSe2oGPbkEyAy40PIxpM',
        'cumbia': '7i3EgwPZeCgy9t2ko5P0Ts',
        'rock-latino': '3cmB6GY8ojluJiJqV8Ci9k',
        'sifon': '6BRFlmT2qiQop5zTDnCkev',  # Categoría especial creada para mi amigo sifon
    }

    if categoria.lower() not in categorias:
        await interaction.response.send_message("Categoría inválida. Las categorías disponibles son: Vocaloid, Jpop, Kpop, Pop, Reggaeton, Cumbia, Rock Latino.", ephemeral=True)
        return

    playlist_id = categorias[categoria.lower()]

    voice_channel = interaction.user.voice.channel
    if not voice_channel:
        await interaction.response.send_message("Debes estar en un canal de voz para jugar a la trivia.", ephemeral=True)
        return

    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if not voice_client:
        voice_client = await voice_channel.connect()
    else:
        await voice_client.move_to(voice_channel)

    await interaction.followup.send(f"Bot conectado al canal de voz: {voice_channel}", ephemeral=True)

    client_credentials_manager = SpotifyClientCredentials(client_id='token', client_secret='token')
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    playlist = sp.playlist(playlist_id, fields='tracks.items(track(name,id,preview_url))')

    tracks = playlist['tracks']['items']
    random_track = random.choice(tracks)
    track_id = random_track['track']['id']
    track = sp.track(track_id)
    preview_url = track['preview_url']

    if not preview_url:
        await interaction.followup.send("No se pudo obtener la vista previa de audio para esta canción. Por favor, intenta con otra categoría.", ephemeral=True)
        await voice_client.disconnect()
        return

    voice_client.play(discord.FFmpegPCMAudio(preview_url))

    await asyncio.sleep(15)
    voice_client.stop()

    await interaction.followup.send(f"Reproduciendo una canción aleatoria de la categoría {categoria} en el canal de voz.", ephemeral=True)

    options = random.sample(tracks, 3)
    options.append(random_track)
    random.shuffle(options)

    options_text = '\n'.join(f"{i+1}. {option['track']['name']}" for i, option in enumerate(options))

    await interaction.followup.send(f"Aquí tienes la trivia de la categoría {categoria}:")
    await interaction.followup.send(f"¿Cuál de las siguientes canciones fue la reproducida?\n{options_text}")

    def check(msg):
        return msg.author == interaction.user and msg.channel == interaction.channel and msg.content.isdigit() and 1 <= int(msg.content) <= 4

    try:
        msg = await bot.wait_for('message', check=check, timeout=20)
    except asyncio.TimeoutError:
        await interaction.followup.send("Tiempo agotado. La respuesta no fue enviada a tiempo.", ephemeral=True)
        await voice_client.disconnect()
        return

    selected_option = options[int(msg.content) - 1]['track']['name']
    if selected_option == random_track['track']['name']:
        await interaction.followup.send("¡Respuesta correcta! Has ganado 100 puntos.", ephemeral=True)
        puntos[str(interaction.user.id)] = puntos.get(str(interaction.user.id), 0) + 100
    else:
        await interaction.followup.send(f"Respuesta incorrecta. La respuesta correcta era: {random_track['track']['name']}.", ephemeral=True)

    await voice_client.disconnect()

bot.run('Token')
