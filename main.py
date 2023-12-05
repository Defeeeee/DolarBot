from enum import Enum
import os
from dotenv import load_dotenv
import requests
import json
from discord.ext import commands, tasks
from itertools import cycle
import discord
from discord import app_commands
from datetime import datetime
import random

class Casa(Enum):
    Blue = 'blue'
    Oficial = 'oficial'
    Solidario = 'solidario'
    Bolsa = 'bolsa'
    CCL = 'contadoconliqui'
    Tarjeta = 'tarjeta'
    Mayorista = 'mayorista'
    Cripto = 'cripto'

client_status = cycle(
    ["Dolar ARG", f"Blue: ARS {json.loads(requests.get(f'https://dolarapi.com/v1/dolares/blue').text)['venta']}"])

load_dotenv()

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        client.tree.clear_commands(guild=guild)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)


intents = discord.Intents.default()

client = MyClient(intents=intents)

guild = discord.Object(id=868582958729150504)


@tasks.loop(seconds=5)
async def change_status():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=next(client_status)))


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    # client.tree.clear_commands(guild=guild)
    # await client.tree.sync(guild=guild)
    change_status.start()


@client.tree.command(description="Lista de comandos")
async def commands(Interaction: discord.Interaction):
    embed = discord.Embed(title="Comandos", color=0x00ff00)
    for command in client.tree.walk_commands():
        embed.add_field(name=f"/{command.name}", value=command.description, inline=False)
    await Interaction.response.send_message(embed=embed)


@client.tree.command(description="Peruaniza al usuario deseado")
@app_commands.describe(user='Usuario a peruanizar')
async def peruano(Interaction: discord.Interaction, user: discord.User):
    embed = discord.Embed(title=f"{user} peruanizado", color=0x00ff00)
    channel = await user.create_dm()
    await Interaction.response.send_message(embed=embed)
    embed2 = discord.Embed(title=f"{Interaction.user} te ha peruanizado", color=0x00ff00)
    embed3 = discord.Embed(title="Peruano", color=0x00ff00)
    embed3.set_footer(text=Interaction.user, icon_url=Interaction.user.avatar)
    await channel.send(embed=embed2)
    for i in range(0, 10):
        await channel.send(embed=embed3)


@client.tree.command(description="Hace un request a la API solicitada")
@app_commands.describe(url='URL de la API')
async def request(Interaction: discord.Interaction, url: str):
    embed = discord.Embed(title=f'Request a {url.replace(" ", "")}', color=0x00ff00)
    try:
        response = requests.get(url.replace(" ", ""))
        formatted_string = json.dumps(response.json(), indent=2)
    except:
        await Interaction.response.send_message("Error al hacer el request", ephemeral=True)
        return
    embed.add_field(name="Response", value=f"```json\n{formatted_string}```", inline=False)
    embed.set_footer(text=f'User: {Interaction.user}', icon_url=Interaction.user.avatar)
    embed.timestamp = Interaction.created_at
    await Interaction.response.send_message(embed=embed)


@client.tree.command(description="Devuelve el valor del dolar solicitado")
@app_commands.describe(casa='Tipo de dolar')
async def dolar(Interaction: discord.Interaction, casa: Casa):
    try:
        response_API = requests.get(f'https://dolarapi.com/v1/dolares/{Casa(casa).value}')
    except:
        await Interaction.response.send_message("Error al hacer el request", ephemeral=True)
        return
    data = response_API.text
    parse_json = json.loads(data)
    embed = discord.Embed(title=f"Dolar {parse_json['nombre']}", color=0x00ff00)
    embed.add_field(name="Venta", value=f"ARS {parse_json['venta']}", inline=False)
    embed.add_field(name="Compra", value=f"ARS {parse_json['compra']}", inline=False)

    embed.set_footer(text=f'User: {Interaction.user}', icon_url=Interaction.user.avatar)
    if not Casa(casa).value == 'tarjeta':
        embed.timestamp = datetime.strptime(parse_json['fechaActualizacion'], '%Y-%m-%dT%H:%M:%S.000Z')
    await Interaction.response.send_message(embed=embed)


client.run(os.getenv('TOKEN'))
