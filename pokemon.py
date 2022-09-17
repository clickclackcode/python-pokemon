import pygame
from pygame.locals import *
import time
import math
import random
import requests
import io
from urllib.request import urlopen

pygame.init()

# create the game window
game_width = 500
game_height = 500
size = (game_width, game_height)
game = pygame.display.set_mode(size)
pygame.display.set_caption('Pokemon Battle')

# define colors
black = (0, 0, 0)
gold = (218, 165, 32)
grey = (200, 200, 200)
green = (0, 200, 0)
red = (200, 0, 0)
white = (255, 255, 255)

# base url of the API
base_url = 'https://pokeapi.co/api/v2'

class Move():
    
    def __init__(self, url):
        
        # call the moves API endpoint
        req = requests.get(url)
        self.json = req.json()
        
        self.name = self.json['name']
        self.power = self.json['power']
        self.type = self.json['type']['name']

class Pokemon(pygame.sprite.Sprite):
    
    def __init__(self, name, level, x, y):
        
        pygame.sprite.Sprite.__init__(self)
        
        # call the pokemon API endpoint
        req = requests.get(f'{base_url}/pokemon/{name.lower()}')
        self.json = req.json()
        
        # set the pokemon's name and level
        self.name = name
        self.level = level
        
        # set the sprite position on the screen
        self.x = x
        self.y = y
        
        # number of potions left
        self.num_potions = 3
        
        # get the pokemon's stats from the API
        stats = self.json['stats']
        for stat in stats:
            if stat['stat']['name'] == 'hp':
                self.current_hp = stat['base_stat'] + self.level
                self.max_hp = stat['base_stat'] + self.level
            elif stat['stat']['name'] == 'attack':
                self.attack = stat['base_stat']
            elif stat['stat']['name'] == 'defense':
                self.defense = stat['base_stat']
            elif stat['stat']['name'] == 'speed':
                self.speed = stat['base_stat']
                
        # set the pokemon's types
        self.types = []
        for i in range(len(self.json['types'])):
            type = self.json['types'][i]
            self.types.append(type['type']['name'])
            
        # set the sprite's width
        self.size = 150
        
        # set the sprite to the front facing sprite
        self.set_sprite('front_default')
    
    def perform_attack(self, other, move):
        
        display_message(f'{self.name} used {move.name}')
        
        # pause for 2 seconds
        time.sleep(2)
        
        # calculate the damage
        damage = (2 * self.level + 10) / 250 * self.attack / other.defense * move.power
        
        # same type attack bonus (STAB)
        if move.type in self.types:
            damage *= 1.5
            
        # critical hit (6.25% chance)
        random_num = random.randint(1, 10000)
        if random_num <= 625:
            damage *= 1.5
            
        # round down the damage
        damage = math.floor(damage)
        
        other.take_damage(damage)
        
    def take_damage(self, damage):
        
        self.current_hp -= damage
        
        # hp should not go below 0
        if self.current_hp < 0:
            self.current_hp = 0
    
    def use_potion(self):
        
        # check if there are potions left
        if self.num_potions > 0:
            
            # add 30 hp (but don't go over the max hp)
            self.current_hp += 30
            if self.current_hp > self.max_hp:
                self.current_hp = self.max_hp
                
            # decrease the number of potions left
            self.num_potions -= 1
        
    def set_sprite(self, side):
        
        # set the pokemon's sprite
        image = self.json['sprites'][side]
        image_stream = urlopen(image).read()
        image_file = io.BytesIO(image_stream)
        self.image = pygame.image.load(image_file).convert_alpha()
        
        # scale the image
        scale = self.size / self.image.get_width()
        new_width = self.image.get_width() * scale
        new_height = self.image.get_height() * scale
        self.image = pygame.transform.scale(self.image, (new_width, new_height))
        
    def set_moves(self):
        
        self.moves = []
        
        # go through all moves from the api
        for i in range(len(self.json['moves'])):
            
            # get the move from different game versions
            versions = self.json['moves'][i]['version_group_details']
            for j in range(len(versions)):
                
                version = versions[j]
                
                # only get moves from red-blue version
                if version['version_group']['name'] != 'red-blue':
                    continue
                    
                # only get moves that can be learned from leveling up (ie. exclude TM moves)
                learn_method = version['move_learn_method']['name']
                if learn_method != 'level-up':
                    continue
                    
                # add move if pokemon level is high enough
                level_learned = version['level_learned_at']
                if self.level >= level_learned:
                    move = Move(self.json['moves'][i]['move']['url'])
                    
                    # only include attack moves
                    if move.power is not None:
                        self.moves.append(move)
                        
        # select up to 4 random moves
        if len(self.moves) > 4:
            self.moves = random.sample(self.moves, 4)
        
    def draw(self, alpha=255):
        
        sprite = self.image.copy()
        transparency = (255, 255, 255, alpha)
        sprite.fill(transparency, None, pygame.BLEND_RGBA_MULT)
        game.blit(sprite, (self.x, self.y))
        
    def draw_hp(self):
        
        # display the health bar
        bar_scale = 200 // self.max_hp
        for i in range(self.max_hp):
            bar = (self.hp_x + bar_scale * i, self.hp_y, bar_scale, 20)
            pygame.draw.rect(game, red, bar)
            
        for i in range(self.current_hp):
            bar = (self.hp_x + bar_scale * i, self.hp_y, bar_scale, 20)
            pygame.draw.rect(game, green, bar)
            
        # display "HP" text
        font = pygame.font.Font(pygame.font.get_default_font(), 16)
        text = font.render(f'HP: {self.current_hp} / {self.max_hp}', True, black)
        text_rect = text.get_rect()
        text_rect.x = self.hp_x
        text_rect.y = self.hp_y + 30
        game.blit(text, text_rect)
        
    def get_rect(self):
        
        return Rect(self.x, self.y, self.image.get_width(), self.image.get_height())

def display_message(message):
    
    # draw a white box with black border
    pygame.draw.rect(game, white, (10, 350, 480, 140))
    pygame.draw.rect(game, black, (10, 350, 480, 140), 3)
    
    # display the message
    font = pygame.font.Font(pygame.font.get_default_font(), 20)
    text = font.render(message, True, black)
    text_rect = text.get_rect()
    text_rect.x = 30
    text_rect.y = 410
    game.blit(text, text_rect)
    
    pygame.display.update()
    
def create_button(width, height, left, top, text_cx, text_cy, label):
    
    # position of the mouse cursor
    mouse_cursor = pygame.mouse.get_pos()
    
    button = Rect(left, top, width, height)
    
    # highlight the button if mouse is pointing to it
    if button.collidepoint(mouse_cursor):
        pygame.draw.rect(game, gold, button)
    else:
        pygame.draw.rect(game, white, button)
        
    # add the label to the button
    font = pygame.font.Font(pygame.font.get_default_font(), 16)
    text = font.render(f'{label}', True, black)
    text_rect = text.get_rect(center=(text_cx, text_cy))
    game.blit(text, text_rect)
    
    return button
        
# create the starter pokemons
level = 30
bulbasaur = Pokemon('Bulbasaur', level, 25, 150)
charmander = Pokemon('Charmander', level, 175, 150)
squirtle = Pokemon('Squirtle', level, 325, 150)
pokemons = [bulbasaur, charmander, squirtle]

# the player's and rival's selected pokemon
player_pokemon = None
rival_pokemon = None

# game loop
game_status = 'select pokemon'
while game_status != 'quit':
    
    for event in pygame.event.get():
        if event.type == QUIT:
            game_status = 'quit'
            
        # detect keypress
        if event.type == KEYDOWN:
            
            # play again
            if event.key == K_y:
                # reset the pokemons
                bulbasaur = Pokemon('Bulbasaur', level, 25, 150)
                charmander = Pokemon('Charmander', level, 175, 150)
                squirtle = Pokemon('Squirtle', level, 325, 150)
                pokemons = [bulbasaur, charmander, squirtle]
                game_status = 'select pokemon'
                
            # quit
            elif event.key == K_n:
                game_status = 'quit'
            
        # detect mouse click
        if event.type == MOUSEBUTTONDOWN:
            
            # coordinates of the mouse click
            mouse_click = event.pos
            
            # for selecting a pokemon
            if game_status == 'select pokemon':
                
                # check which pokemon was clicked on
                for i in range(len(pokemons)):
                    
                    if pokemons[i].get_rect().collidepoint(mouse_click):
                        
                        # assign the player's and rival's pokemon
                        player_pokemon = pokemons[i]
                        rival_pokemon = pokemons[(i + 1) % len(pokemons)]
                        
                        # lower the rival pokemon's level to make the battle easier
                        rival_pokemon.level = int(rival_pokemon.level * .75)
                        
                        # set the coordinates of the hp bars
                        player_pokemon.hp_x = 275
                        player_pokemon.hp_y = 250
                        rival_pokemon.hp_x = 50
                        rival_pokemon.hp_y = 50
                        
                        game_status = 'prebattle'
            
            # for selecting fight or use potion
            elif game_status == 'player turn':
                
                # check if fight button was clicked
                if fight_button.collidepoint(mouse_click):
                    game_status = 'player move'
                    
                # check if potion button was clicked
                if potion_button.collidepoint(mouse_click):
                    
                    # force to attack if there are no more potions
                    if player_pokemon.num_potions == 0:
                        display_message('No more potions left')
                        time.sleep(2)
                        game_status = 'player move'
                    else:
                        player_pokemon.use_potion()
                        display_message(f'{player_pokemon.name} used potion')
                        time.sleep(2)
                        game_status = 'rival turn'
                        
            # for selecting a move
            elif game_status == 'player move':
                
                # check which move button was clicked
                for i in range(len(move_buttons)):
                    button = move_buttons[i]
                    
                    if button.collidepoint(mouse_click):
                        move = player_pokemon.moves[i]
                        player_pokemon.perform_attack(rival_pokemon, move)
                        
                        # check if the rival's pokemon fainted
                        if rival_pokemon.current_hp == 0:
                            game_status = 'fainted'
                        else:
                            game_status = 'rival turn'
            
    # pokemon select screen
    if game_status == 'select pokemon':
        
        game.fill(white)
        
        # draw the starter pokemons
        bulbasaur.draw()
        charmander.draw()
        squirtle.draw()
        
        # draw box around pokemon the mouse is pointing to
        mouse_cursor = pygame.mouse.get_pos()
        for pokemon in pokemons:
            
            if pokemon.get_rect().collidepoint(mouse_cursor):
                pygame.draw.rect(game, black, pokemon.get_rect(), 2)
        
        pygame.display.update()
        
    # get moves from the API and reposition the pokemons
    if game_status == 'prebattle':
        
        # draw the selected pokemon
        game.fill(white)
        player_pokemon.draw()
        pygame.display.update()
        
        player_pokemon.set_moves()
        rival_pokemon.set_moves()
        
        # reposition the pokemons
        player_pokemon.x = -50
        player_pokemon.y = 100
        rival_pokemon.x = 250
        rival_pokemon.y = -50
        
        # resize the sprites
        player_pokemon.size = 300
        rival_pokemon.size = 300
        player_pokemon.set_sprite('back_default')
        rival_pokemon.set_sprite('front_default')
        
        game_status = 'start battle'
        
    # start battle animation
    if game_status == 'start battle':
        
        # rival sends out their pokemon
        alpha = 0
        while alpha < 255:
            
            game.fill(white)
            rival_pokemon.draw(alpha)
            display_message(f'Rival sent out {rival_pokemon.name}!')
            alpha += .4
            
            pygame.display.update()
            
        # pause for 1 second
        time.sleep(1)
        
        # player sends out their pokemon
        alpha = 0
        while alpha < 255:
            
            game.fill(white)
            rival_pokemon.draw()
            player_pokemon.draw(alpha)
            display_message(f'Go {player_pokemon.name}!')
            alpha += .4
            
            pygame.display.update()
        
        # draw the hp bars
        player_pokemon.draw_hp()
        rival_pokemon.draw_hp()
        
        # determine who goes first
        if rival_pokemon.speed > player_pokemon.speed:
            game_status = 'rival turn'
        else:
            game_status = 'player turn'
            
        pygame.display.update()
        
        # pause for 1 second
        time.sleep(1)
        
    # display the fight and use potion buttons
    if game_status == 'player turn':
        
        game.fill(white)
        player_pokemon.draw()
        rival_pokemon.draw()
        player_pokemon.draw_hp()
        rival_pokemon.draw_hp()
        
        # create the fight and use potion buttons
        fight_button = create_button(240, 140, 10, 350, 130, 412, 'Fight')
        potion_button = create_button(240, 140, 250, 350, 370, 412, f'Use Potion ({player_pokemon.num_potions})')

        # draw the black border
        pygame.draw.rect(game, black, (10, 350, 480, 140), 3)
        
        pygame.display.update()
        
    # display the move buttons
    if game_status == 'player move':
        
        game.fill(white)
        player_pokemon.draw()
        rival_pokemon.draw()
        player_pokemon.draw_hp()
        rival_pokemon.draw_hp()
        
        # create a button for each move
        move_buttons = []
        for i in range(len(player_pokemon.moves)):
            move = player_pokemon.moves[i]
            button_width = 240
            button_height = 70
            left = 10 + i % 2 * button_width
            top = 350 + i // 2 * button_height
            text_center_x = left + 120
            text_center_y = top + 35
            button = create_button(button_width, button_height, left, top, text_center_x, text_center_y, move.name.capitalize())
            move_buttons.append(button)
            
        # draw the black border
        pygame.draw.rect(game, black, (10, 350, 480, 140), 3)
        
        pygame.display.update()
        
    # rival selects a random move to attack with
    if game_status == 'rival turn':
        
        game.fill(white)
        player_pokemon.draw()
        rival_pokemon.draw()
        player_pokemon.draw_hp()
        rival_pokemon.draw_hp()
        
        # empty the display box and pause for 2 seconds before attacking
        display_message('')
        time.sleep(2)
        
        # select a random move
        move = random.choice(rival_pokemon.moves)
        rival_pokemon.perform_attack(player_pokemon, move)
        
        # check if the player's pokemon fainted
        if player_pokemon.current_hp == 0:
            game_status = 'fainted'
        else:
            game_status = 'player turn'
            
        pygame.display.update()
        
    # one of the pokemons fainted
    if game_status == 'fainted':
        
        alpha = 255
        while alpha > 0:
            
            game.fill(white)
            player_pokemon.draw_hp()
            rival_pokemon.draw_hp()
            
            # determine which pokemon fainted
            if rival_pokemon.current_hp == 0:
                player_pokemon.draw()
                rival_pokemon.draw(alpha)
                display_message(f'{rival_pokemon.name} fainted!')
            else:
                player_pokemon.draw(alpha)
                rival_pokemon.draw()
                display_message(f'{player_pokemon.name} fainted!')
            alpha -= .4
            
            pygame.display.update()
            
        game_status = 'gameover'
        
    # gameover screen
    if game_status == 'gameover':
        
        display_message('Play again (Y/N)?')
        
pygame.quit()