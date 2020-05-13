from iqoptionapi.stable_api import IQ_Option
import time, json, logging, configparser
from datetime import datetime
from datetime import timedelta
from dateutil import tz
from decimal import Decimal

try:
    file = open('sinais.txt')
except IOError:
    print('Ocorreu um erro, arquivo [sinais.txt] não encontrado')

arquivo = configparser.RawConfigParser()
arquivo.read('config.txt')

email = arquivo.get('GERAL', 'email')
senha = arquivo.get('GERAL', 'senha')
error_password = """{"code":"invalid_credentials","message":"You entered the wrong credentials. Please check that the login/password is correct."}"""

#tf = int(arquivo.get('GERAL', 'timeframe'))
qtd_mg = int(arquivo.get('GERAL', 'qtd_mg'))

API = IQ_Option(email, senha)
check, reason = API.connect()

if check:
    print('CONECTADO COM SUCESSO!')
    print('--' * 40)

    tf = int(input('Digite o timeframe: '))

    def perfil():
	    perfil = json.loads(json.dumps(API.get_profile_ansyc()))
	    return perfil

    def timestamp_converter(x):
        hora = datetime.strptime(datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
        hora = hora.replace(tzinfo=tz.gettz('GMT'))
        return str(hora.astimezone(tz.gettz('America/Sao Paulo')))[:-6]

    def stringToTimestamp(texto: str) -> int:
      #Converte data e hora no formato dia/mes/ano hora:minuto:segundo para timestamp
      return int(time.mktime(datetime.strptime(texto, '%d/%m/%Y %H:%M:%S').timetuple()))

    def listaDeEntradas():
        #Carrega a lista de sinais de um arquivo txt
        with open('sinais.txt', 'r') as sinais:
            listaSinais = sinais.read()
            listaSinais = listaSinais.split('\n')
        return listaSinais


    def confereLista(lista):
        print('\n')
        print('    Iniciando Conferência')
        print('\n')

        for linha in lista:
            linha = linha.split(',')

            if len(linha) == 3:

                agora = datetime.now()
                data_sinal = agora.strftime('%d/%m/%Y')
                hora_sinal = (str(linha[0] + ':00'))
                ativo = linha[1]
                if linha[2][:-1] == 'CAL':
                    acao = 'CALL'
                else:
                    acao = linha[2][:-1]
                timestampLinha = stringToTimestamp(f'{data_sinal} {hora_sinal}')
                data_sinal = timestamp_converter(timestampLinha)
                
                total = []
                timeframe = tf * 60
                tempo = time.time()
                td = timedelta(minutes=tf)
                total_gale = qtd_mg + 1
                gale=0

                for i in range(1):
                    X = API.get_candles(ativo, timeframe, 300, tempo)
                    total = X+total
                    tempo = int(X[0]['from'])-1

                    for velas in total:
                        data_vela = timestamp_converter(velas['from'])
                        data_vela = datetime.strptime(data_vela, '%Y-%m-%d %H:%M:%S')
                        data_sinal = datetime.strptime(str(data_sinal), '%Y-%m-%d %H:%M:%S')

                        for t in range(total_gale):
                            if data_vela == data_sinal :
                                tipo_vela  = Decimal(velas['open']) - Decimal(velas['close'])

                                if tipo_vela<0 :
                                    direcao_vela = 'CALL'
                                elif tipo_vela >0 :
                                    direcao_vela = 'PUT'
                                elif tipo_vela ==0:
                                    direcao_vela = 'D'

                                if direcao_vela == acao.upper():
                                    result = 'WIN'
                                    if gale < total_gale:
                                        if gale == 0:
                                            print('{}   {}  {}={}'.format(hora_sinal, ativo, acao, result))
                                            gale = 0
                                        else:
                                            print('{}   {}  {}={}GALE'.format(hora_sinal, ativo, acao, result))
                                            gale = 0
                                    break   

                                else:
                                    data_vela = data_vela + td
                                    data_sinal = data_sinal + td

                                    result = 'LOSS'
                                    gale += 1
                                    if gale == total_gale:
                                        print('{}   {}  {}={}'.format(hora_sinal, ativo, acao, result)) 

                                    break

    lista = listaDeEntradas()
    confereLista(lista)
    
else:  
    if reason=="[Errno -2] Name or service not known":
        print("No Network")
    elif reason==error_password:
        print("Error Password")