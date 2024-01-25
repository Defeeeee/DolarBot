from enum import Enum
import os
from dotenv import load_dotenv
import requests
import json
from discord.ext import commands, tasks
from itertools import cycle
import discord
from discord import app_commands
from datetime import datetime, date, timedelta
import subprocess as sp
import random


class Casa(Enum):
    Blue = 'blue'
    Oficial = 'oficial'
    Bolsa = 'bolsa'
    CCL = 'contadoconliqui'
    Tarjeta = 'tarjeta'
    Mayorista = 'mayorista'
    Cripto = 'cripto'


def dolarstr(tipo):
    return f"{Casa._value2member_map_[tipo].name}: ARS {json.loads(requests.get(f'https://dolarapi.com/v1/dolares/{tipo}').text)['venta']}"


# por cada item de Casa  agrega un campo con el nombre del item y el valor del dolar intercalados por "Dolar ARG

client_status = cycle(["Dolar ARG", dolarstr(Casa.Blue.value), "Dolar ARG", dolarstr(Casa.Oficial.value),
                       "Dolar ARG", dolarstr(Casa.Bolsa.value), "Dolar ARG", dolarstr(Casa.CCL.value), "Dolar ARG",
                       dolarstr(Casa.Tarjeta.value),
                       "Dolar ARG", dolarstr(Casa.Mayorista.value), "Dolar ARG", dolarstr(Casa.Cripto.value)])

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
    await client.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name=next(client_status)))


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


@client.tree.command(description="Run command")
@app_commands.describe(command='Command to run')
async def run(Interaction: discord.Interaction, command: str):
    if not Interaction.user.id == 333215596944818177:
        await Interaction.response.send_message("No tenes permiso para usar este comando", ephemeral=True)
        return
    embed = discord.Embed(title=f'Run command {command}', color=0x00ff00)
    try:
        result = sp.run(command, stdout=sp.PIPE, stderr=sp.PIPE, shell=True, timeout=5)
        formatted_string = result.stdout.decode('utf-8')

    except:
        await Interaction.response.send_message("Error al correr el comando", ephemeral=True)
        return
    embed.add_field(name="Response", value=f"```{formatted_string}```", inline=False)
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

class Intervalo(Enum):
    Dia = 0
    Semana = 1
    Mes = 2
    Año = 3

@client.tree.command(description="Devuelve la variacion en el intervalo deseado de un dolar")
@app_commands.describe(casa='Tipo de dolar', intervalo='Intervalo de tiempo')
async def variacion(Interaction: discord.Interaction, casa: Casa, intervalo: Intervalo):
    try:
        response_API = requests.get(f'https://dolarapi.com/v1/dolares/{Casa(casa).value}')
        data = response_API.text
        parse_json = json.loads(data)
        actual = parse_json['compra']
    except:
        await Interaction.response.send_message("Error al hacer el request", ephemeral=True)
        return

    match Intervalo(intervalo).value:
        case 0:
            fecha = (datetime.today() - timedelta(days=1))
        case 1:
            fecha = (datetime.today() - timedelta(days=7))
        case 2:
            if datetime.today().month in [1, 3, 5, 7, 8, 10, 12]:
                fecha = (datetime.today() - timedelta(days=31))
            else:
                fecha = (datetime.today() - timedelta(days=30))
        case 3:
            fecha = (datetime.today() - timedelta(days=365))

    try:
        api_intervalo = requests.get(f'https://api.argentinadatos.com/v1/cotizaciones/dolares/{Casa(casa).value}/{fecha.strftime("%Y/%m/%d")}')
        datah = api_intervalo.text
        parse_jsonh = json.loads(datah)
        historico = parse_jsonh['compra']
    except:
        await Interaction.response.send_message("Error al hacer el request historico", ephemeral=True)
        return

    try:
        variacion = round((actual - historico) / historico * 100, 2)
    except:
        variacion = 0

    embed = discord.Embed(title=f"Variacion {Casa(casa).name}", color=0x00ff00)
    embed.add_field(name="Variacion", value=f"{variacion}%", inline=False)
    embed.add_field(name= f'Actual ({datetime.today().strftime("%d/%m/%Y")})', value=f"ARS {actual}", inline=False)
    embed.add_field(name= f'Historico ({fecha.strftime("%d/%m/%Y")})', value=f"ARS {historico}", inline=False)
    embed.set_footer(text=f'User: {Interaction.user}', icon_url=Interaction.user.avatar)
    await Interaction.response.send_message(embed=embed)



client.run(os.getenv('TOKEN'))
