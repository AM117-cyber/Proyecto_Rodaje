from typing import Any
import string
from sly import Lexer, Parser

class MyLexer(Lexer):

    def __init__(self, scene_op,inoutop,momnent_op):
        self.Scene_options=scene_op
        self.In_out_options=inoutop
        self.Moment_options=momnent_op


    tokens={SEPARADOR, SCENE_OPTIONS, IN_OUT_OPTIONS, MOMENT_OPTIONS, NUMBER,TEXT}

    ignore=' \t\n'

    SCENE_OPTIONS=rf'{Scene_options}'
    IN_OUT_OPTIONS = rf'{In_out_options}'
    MOMENT_OPTIONS = rf'{Moment_options}'
    NUMBER = r'\d+'
    SEPARADOR = r'\-|\-\-|/|\.'
    TEXT = r'[^\s\n\t]+'
    # TEXT = r'[a-zA-ZáéíóúñÁÉÍÓÚÑ0-9!@#$%^&*()_+=\[\]{};:\'",.<>/?\\|`~\-«»¿¡!]+'

class MyParser(Parser):
    tokens = MyLexer.tokens

    # Regla principal de la gramática que reconoce la estructura general
    @_('opcional_escena opcional_numero in_out_opcion texto_con_separadores moment_options')
    def entrada(self, p):
        return ( p.opcional_escena, p.opcional_numero, p.in_out_opcion, p.texto_con_separadores, p.moment_options)

    # Reglas para manejar la opción de tener o no SCENE_OPTIONS
    @_('SCENE_OPTIONS')
    def opcional_escena(self, p):
        return p.SCENE_OPTIONS

    @_('empty')
    def opcional_escena(self, p):
        return None

    # Reglas para manejar la opción de tener o no NUMBER
    @_('NUMBER SEPARADOR')
    def opcional_numero(self, p):
        return p.NUMBER

    @_('empty')
    def opcional_numero(self, p):
        return None

    # Regla para manejar IN_OUT_OPTIONS seguido de un separador
    @_('IN_OUT_OPTIONS SEPARADOR')
    def in_out_opcion(self, p):
        return p.IN_OUT_OPTIONS

    @_('TEXT secuencia_de_texto')
    def texto_con_separadores(self, p):
        return f"{p.TEXT} {p.secuencia_de_texto}"
    
    @_('SEPARADOR TEXT secuencia_de_texto ')
    def secuencia_de_texto(self, p):
        return f"{p.SEPARADOR} {p.TEXT} {p.secuencia_de_texto}"
    
    @_('TEXT secuencia_de_texto')
    def secuencia_de_texto(self, p):
        return f"{p.TEXT} {p.secuencia_de_texto}"

    @_('TEXT SEPARADOR')
    def secuencia_de_texto(self, p):
        return p.TEXT
    
    @_('SEPARADOR')
    def secuencia_de_texto(self, p):
        return ''
    
    @_('MOMENT_OPTIONS')
    def moment_options(self, p):
        return p.MOMENT_OPTIONS

    # Regla para manejar casos vacíos (ausencia de SCENE_OPTIONS o NUMBER)
    @_('')
    def empty(self, p):
        return None

    # Manejo de errores sintácticos
    def error(self, p):
        if p:
            print(f"Error de sintaxis en el token {p.type}, valor {p.value}")
        else:
            print("Error de sintaxis en el final de la entrada")

class Scene_separator(object):
    def __init__(self, scene_options, in_out_options, moment_options):

        scene_options2 = sorted(scene_options, key=len, reverse=True)
        in_out_options2 = sorted(in_out_options, key=len, reverse=True)
        moment_options2 = sorted(moment_options, key=len, reverse=True)
        Scene = '|'.join(scene_options2)
        In_out = '|'.join(in_out_options2)
        Moment = '|'.join(moment_options2)

        self.lexer = MyLexer(Scene,In_out,Moment)
        self.parser = MyParser()
        self.Scene_options = scene_options
        self.In_out_options = in_out_options
        self.Moment_options = moment_options
  
    def __call__(self, script_text_per_page):
        scenes_headings = []
        past_line=""
        index_scene=1
        text=""
        old_result=None
        last_page=None
        for page in script_text_per_page.keys():
            last_page=page
            page_content = script_text_per_page[page]
            page_content = page_content.split('\n')
            for line in page_content:

                result = self.parser.parse(self.lexer.tokenize(line.strip()))
                if old_result is None:
                    if result is None:
                        past_line+=" "
                        result2= self.parser.parse(self.lexer.tokenize(past_line+line.strip()))
                        if result2 is None:
                            past_line=line.strip()
                        else:
                            old_result=result2
                            past_line=""
                    else:
                        old_result=result
                        past_line=""
                    continue
                elif result is None:
                    past_line+=" "
                    result3 = self.parser.parse(self.lexer.tokenize(past_line+line.strip()))
                    if result3 is None:
                        text+= "\n"+ past_line.strip()
                        past_line=line.strip()
                    else:
                        if old_result[1] is None:
                            scenes_headings.append(Scene(index_scene,old_result[2],old_result[3],old_result[4],self.calculate_time(len(text)),page,None,None,text.strip()))
                        else:
                            scenes_headings.append(Scene(old_result[1],old_result[2],old_result[3],old_result[4],self.calculate_time(len(text)),page,None,None,text.strip()))
                        past_line=""
                        text=""
                        old_result=result3
                        index_scene+=1
                else:
                    text+= "\n"+ past_line.strip()
                    if old_result[1] is None:
                        scenes_headings.append(Scene(index_scene,old_result[2],old_result[3],old_result[4],self.calculate_time(len(text)),page,None,None,text.strip()))
                    else:
                        scenes_headings.append(Scene(old_result[1],old_result[2],old_result[3],old_result[4],self.calculate_time(len(text)),page,None,None,text.strip()))
                    past_line=""
                    text=""
                    old_result=result
                    index_scene+=1
        if old_result != None:
            text+= "\n"+past_line.strip()
            if old_result[1] is None:
                scenes_headings.append(Scene(index_scene,old_result[2],old_result[3],old_result[4],self.calculate_time(len(text)),last_page,None,None,text.strip()))
            else:
                scenes_headings.append(Scene(old_result[1],old_result[2],old_result[3],old_result[4],self.calculate_time(len(text)),last_page,None,None,text.strip()))

        return scenes_headings
    

    @staticmethod
    def calculate_time(char_count):
        # quotient, remainder = divmod(a, b)
        minutes, seconds = divmod(char_count, 1020)
        return (minutes, seconds)

class Scene(object):
    def __init__(self, number, in_out, place, moment, time, page,characters,continuity,text):
        self.number = number
        self.in_out = in_out
        self.place = place
        self.moment = moment
        self.time = time
        self.page = page
        self.characters=characters
        self.continuity=continuity
        self.text=text