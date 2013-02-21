#!/usr/bin/python
# -*- encoding: utf-8 -*-
# Funcao para adicinaor e remover usuario do sistema - UFC
# Italo Pessoa - italoneypessoa@gmail.com, 16 de Fevereiro de 2013

# atualização 2.0, adicionar funcoes e estruturas no código para permitir que
# sejam utilizadas as configurações de /etc/adduser.conf

import getpass
import sys
import crypt
import os
import shutil
import copy
import time
import re
from datetime import datetime

new_password="" # senha do usuario

passwd_filename="root/etc/passwd"
shadow_filename="root/etc/shadow"
group_filename="root/etc/group"
gshadow_filename="root/etc/gshadow"
addUserErrorLog="add.log"

# dicionario paa armazenar os valores das propriedades
addUserProperties={'DSHELL':None,'DHOME':None,'GROUPHOMES':None,'LETTERHOMES':None,'SKEL':None,
'FIRST_SYSTEM_UID':None,'LAST_SYSTEM_UID':None,'FIRST_SYSTEM_GID':None,'LAST_SYSTEM_GID':None,
'FIRST_UID':None,'LAST_UID':None,'FIRST_GID':None,'LAST_GID':None,'USERGROUPS':None,'USERS_GID':None,
'DIR_MODE':None,'SETGID_HOME':None,'QUOTAUSER':None,'SKEL_IGNORE_REGEX':None,'EXTRA_GROUPS':None,
'ADD_EXTRA_GROUPS':None,'NAME_REGEX':None}

# funcao para criar id de usuario e/ou grupo
# a partir dos id's ja utilizados
# idsFile = arquivo onde se encontram as informacoes
# de usuario ou grupo
# exemplo: /etc/passwd, /etc/group
def getNewId(idsFile):
	new_id=0

	# variavel para armazenar arquivo
	passwd = open(idsFile,'r')

	# realizar leitura das linhas
	# TODO pode ser utilizado diretamente
	for linha in passwd.readlines():
		# recuperar apenas o id
		max_id=int(linha.strip('\n').split(':')[2])

		# verificar se o id é maior que o atual
		if  max_id < 9999 and max_id > new_id:
			new_id = max_id

	new_id=new_id+1
	# retornar o novo id
	return new_id

# funcao para requisicao de senha do usuario
def getPassword():
	# o operador global se faz necessario para modificar o valor da variavel global "new_password"
	global new_password

	# requisitar ao usuario que informa a senha
	new_password = getpass.getpass("Digite a nova senha UNIX:")	

	# requisitar a confirmacao da senah
	confirm_password = getpass.getpass("Redigite a nova senha UNIX:")

	# caso a senha nao seha informada repetir o precesso anterior
	while new_password == "":
		# informar ao usuario que a senha noa foi digitada
		print "Nenhuma senha informada"
		new_password = getpass.getpass("Digite a nova senha UNIX:")	
		confirm_password = getpass.getpass("Redigite a nova senha UNIX:")

	# verificar se a confirmacao da senha esta correta
	if new_password != confirm_password:
		# caso nao esteja informar o erro
		print "Sorry, passwords do not match"
		print "passwd: Erro na manipulação de token de autenticação"
		print "passwd: Senha não alterada"

		# perguntar ao usuario se deseja inserir a senha novamente
		res=raw_input("Tentar de novo? [y/N]")

		# caso afirmativo repetir o precesso de requisicao de senha
		if re.match('[sSyY]',res):
			getPassword()
		# caso negativo salvar usuario sem senha '!'
		else:
			new_password="!"

# funcao para copiar arquivos
# src = diretorio origem dos arquivos
# dst = diretorio destino, onde os arquivos devem ser copiados
def copyFiles(src,dst):
	for f in os.listdir(src):
		shutil.copy(src+f,dst)

# funcao para remover o usuario
# username = nome do usuario a ser removido
def delUser(username):

	# realizar a leitura de todos os arquivos e armazenados em listas
	passwdLines = open(passwd_filename,'r').readlines()
	shadowLines = open(shadow_filename,'r').readlines()
	groupLines = open(group_filename,'r').readlines()
	gshadowLines = open(gshadow_filename,'r').readlines()


	# bkp das informacoes das listas
	_bkp_PasswdLines = copy.copy(passwdLines)
	_bkp_ShadowLines = copy.copy(shadowLines)
	_bkp_GroupLines = copy.copy(groupLines)
	_bkp_GshadowLines = copy.copy(gshadowLines)

	# TODO realizar copia das listas atuais, no caso de erro
	# restaurar os arquivos

	# realizar a verificacao em todas as lista
	# para encontrar informacoes referentes ao usuario informado
	for u in passwdLines:
		if u.split(':')[0] == username:
	 		# caso encontre o usuario remover da lista
			passwdLines.remove(u)

	for s in shadowLines:
		if s.split(':')[0] == username:
			shadowLines.remove(s)

	for g in groupLines:
		if g.split(':')[0] == username:
			groupLines.remove(g)

	for gs in gshadowLines:
		if gs.split(':')[0] == username:
			gshadowLines.remove(gs)
	
	# abrir arquivos para escrita
	passwd = open(passwd_filename,'w')
	shadow = open(shadow_filename,'w')
	group = open(group_filename,'w')
	gshadow = open(gshadow_filename,'w')

	try:

		# gravar nova lista nos arquivos especificos
		print "Removendo o usuário `"+username+"' ..."
		# PASSWD
		passwd.writelines(passwdLines)

		print "Aviso: o grupo `"+username+"' não possui mais membros."
		# GROUP
		group.writelines(groupLines)

		# SHADOW
		shadow.writelines(shadowLines)

		# GSHADOW
		gshadow.writelines(gshadowLines)

		print "Concluído."

	except Exception, e:
		print 'Erro ao remover usuário '+ username +"."

		# restaurar informacoes
		# PASSWD
		passwd.writelines(_bkp_PasswdLines)
		# GROUP
		group.writelines(_bkp_ShadowLines)
		# SHADOW
		shadow.writelines(_bkp_GroupLines)
		# GSHADOW
		gshadow.writelines(_bkp_GshadowLines)

		errorLog(e.message)

	finally:
		# fechar os arquivos
		passwd.close()
		group.close()
		shadow.close()
		gshadow.close()

# funcao para adicionar novo usuario
# username = nome do usuario
# home = diretorio padrao do usuario
# senha = senha do usuario
def addUser(username,homeDir=None,user_pass=None):

	# TODO os nomes podem ser substituidos por variaveis
	# verificar se é utilizado regez para validar nome de usuario
	if addUserProperties['NAME_REGEX'] != None:
		# verificar se o nome do usuario e valido
		usernameValidator(addUserProperties['NAME_REGEX'],username)

	print "Adicionando o usuário `"+username+"' ..."
	
	# recuperar id do novo usuario
	uid=getNewId(passwd_filename)

	# verificar se foi informado um caminho diferente
	# do padrão para a home do usuario
	if homeDir == None:
		homeDir="/home/"+username

	# criar grupo para o usuario e recuperar o id do grupo
	gid=addGroup(username,uid)

	print "Criando diretório pessoal `"+homeDir+"' ..."
	
	# criar diretorio pessoal do usuario
	os.mkdir(homeDir)

	# modificar permissoes de acesso da pasta pessoal do usuario
	# verificar se é utilizado valor para acesso ao diretorio do usuario
	if addUserProperties['DIR_MODE'] != None:
		# se possuir utilizar valor indicado
		os.chmod(homeDir,int(addUserProperties['DIR_MODE']))
	else:
		# senao, utilizar um valor padrao
		os.chmod(homeDir,0755)

	# modificar dono e grupo do diretorio pessoal
	os.chown(homeDir,uid,gid)

	print "Copiando arquivos  de `/etc/skel' ..."

	# copiar arquivos padrao para o diretorio pessoal do usuario
	# verificar se e indicado o diretorio skel
	if addUserProperties['DIR_MODE'] != None:
		copyFiles(addUserProperties['DIR_MODE'],homeDir)
	else:
		# senao utilizar um diretorio padrao
		copyFiles('/etc/skel/',homeDir)

	# criar senha do usuario se for utilizado o modo iterativo
	if user_pass == None:
		getPassword()

	# adicionar ao shadow
	# abrir arquivo shadow no modo append
	shadow_file=open(shadow_filename,'a')

	# o operador global se faz necessario para modificar o valor da variavel global "new_password"
	global new_password
	
	# se nao utilizar o modo iterativo
	if user_pass != None and user_pass != "":
		new_password=user_pass

	# verificar se o usuario possui senha
	if new_password != "!":

		# data atual ##/##/#### ##:##:##
		time=datetime.now()

		aux1=str(time.year)[1:2] # 2 primeiros digitos do ano
		aux2=str(time.year)[3:4] # 2 ultimos digitos do ano

		# sal para gerar a senha, combinacao
		# dia, mes, ano1,minuto,ano2,segundos,mes
		salt=str(time.day)+str(time.hour)+aux1+str(time.minute)+aux2+str(time.second)+str(time.month)
		salt="$6$"+salt+"$"

		# criptografar senha
		new_password=crypt.crypt(new_password,salt)

	# salvar informacoes no shadow
	shadow_file.write(username+":"+new_password+":15633:0:99999:7:::\n")

	# fechar arquivo
	shadow_file.close()

	print "Modificando informações de usuário para "+username

	# recuperar restante das informacoes do usuario se utilizar o modo iterativo

	complete_name = ""
	class_number=""
	work_phone=""
	home_phone=""
	other=""

	# se nao utilizar o modo iterativo
	if user_pass != None:
		complete_name = username.replace(username[0],username[0].upper())
	else:
		print "Informe o novo valor ou pressione ENTER para aceitar o valor padrão"
		complete_name = raw_input("\tNome Completo []: ")
		class_number=raw_input("\tNúmero da Sala []: ")
		work_phone=raw_input("\tFone de Trabalho []: ")
		home_phone=raw_input("\tFone Doméstico []: ")
		other=raw_input("\tOutro []: ")

	res=""
	# se utilizar o modo iterativo
	if user_pass == None:
		res=raw_input("Esta informação está correta?[S/n]")
		while not re.match('[sSyY]',res):
			complete_name = raw_input("\tNome Completo []: ")
			class_number=raw_input("\tNúmero da Sala []: ")
			work_phone=raw_input("\tFone de Trabalho []: ")
			home_phone=raw_input("\tFone Doméstico []: ")
			other=raw_input("\tOutro []: ")
			res=raw_input("Esta informação está correta?[S/n]")

	# abrir passwd no modo apped
	passwd_file=open(passwd_filename,'a')

	numbers=str(class_number)+","+work_phone+","+home_phone
	
	if(other != ""):
		numbers=numbers+","+other

	# salvar informacoes no passwd
	passwd_file.write(username+":x:"+str(uid)+":"+str(gid)+":"+complete_name+","+numbers+":"+homeDir+":/bin/bash\n")

	# fechar arquivo
	passwd_file.close()

# funcao para adicinar grupo
# username = nome do usuario
# userid = id do usuario
def addGroup(username,userid):

	# recuperar id do novo grupo
	gid=getNewId(group_filename)
	
	# variavel que contem as informacoes do grupo
	group = username+":x:"+str(gid)	
	print "Adicionando novo grupo `"+username+"' ("+str(gid)+")..."
	# adicionar ao gshadow
	
	# abrir arquivo no modo append
	gshadow_file=open(gshadow_filename,'a')

	# salvar informacoes do grupo
	gshadow_file.write(username+":!::\n")

	# fechar arquivo
	gshadow_file.close()

	print "Adicionando novo usuário `"+username+"' ("+str(userid)+") ao grupo `"+username+"' ..." 
	
	# abrir arquivo no modo append
	group_file=open(group_filename,'a')

	# salvar informacoes do grupo
	group_file.write(group+":\n")

	# fechar arquivo
	group_file.close()

	# retornar o id do grupo salvo
	return gid

# funcao para salvar mensagens de erro em arquivo de log
def errorLog(error):
	logTime=time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())

	log=open(addUserErrorLog,'a')
	log.write('[-] '+logTime+' - '+ error+'\n')
	log.close()

# funcao para pesquisar usuario
# username = nome do usuario
# file = arquivo de usuarios
def findUser(username,file):
	# ler todas as linhas do arquivo de usuarios
	for u in open(file,'r').readlines():
		# se o usuario existir retornar seu nome
		if u.split(':')[0] == username:
			return username

	return None

# funcao para verificar se diretorio existe
# path = caminho completo do diretório
def findDir(path):
	# guardar apenas o nome do diretorio
	homeDir=path.split('/')[-1]
	#remover diretorio do path
	path=path.replace(homeDir,'')
	# verificar todos os arquivos do path atual
	for d in os.listdir(path):
		# retornar o nome do diretorio caso ele exista
		if os.path.isdir(path+homeDir) and d == homeDir:
			return d

	return None

def main():
	
	# o carregamento das propriedades deve ser feito na funcao main devido
	# o dicionario global de propriedades, que não pode ser acessado antes da
	# funcao principal ser executada
	global addUserProperties
	try:
		# recuperar valores das propriedades
		addUserProperties=getAddUserProperties('root/etc/adduser.conf',addUserProperties)
	except Exception, e:
		# Exibir mensagemd e erro
		print "Erro ao carregar configurações. Tente novamente."
		# enviar mensagem de erro para log
		errorLog("Erro ao carregar configurações:" + e.message);
		# retornar codigo de erro
		exit(3) # erro ao carregar configuracoes

	# addUser add|del usuario home senha
	if len(sys.argv) < 3:
		print "Informe os parâmetros necessários\n[add|del] <username> [<homedir>] [<password>]"
	else:
		# se a funcao for adicionar
		if sys.argv[1] == 'add':
			# se utilzar o modo iterativo
			if findUser(sys.argv[2],passwd_filename) != None:
				print 'Usuário \''+sys.argv[2]+'\' já existe.'
				errorLog('Usuário \''+sys.argv[2]+'\' já existe.')
				exit(1) # usuario ja existe
			elif findDir(sys.argv[3]) != None:
				print 'Diretório \''+sys.argv[3]+'\' já existe.'
				errorLog('Diretório \''+sys.argv[3]+'\' já existe.')
				exit(2) # diretorio ja existe
			if len(sys.argv) == 4:
				# nao e informado a senha
				addUser(username=sys.argv[2],homeDir=sys.argv[3])
			elif len(sys.argv) == 5:
				# nao utilizar o modo iterativo, informando a senha
				addUser(username=sys.argv[2],homeDir=sys.argv[3],user_pass=sys.argv[4])
		# se a funcao for remover usuario
		elif sys.argv[1] == 'del':
			delUser(username=sys.argv[2])
		# funcao invalida
		else:
			print 'A opção \''+sys.argv[1]+'\' não existe.'

# funcao ara carregar os valores das propriedades das configuraoes
# de adduser
# conf = arquivo de configuracao
# properties = dicionario contendo as propriedades
def getAddUserProperties(conf,properties):
	# percorrer cada linha do arquivo de configuracao
	for l in open(conf,'r').readlines():
		# verificar cada chave do dicianario
		for k in properties.keys():
			# se a linha contiver a chave
			if re.match(k+'=',l):
				# recuperar o valor da propriedade
				propertieValue=l.strip('\n').split('=')[1]
				# se estiver vazio mudar para None
				if propertieValue == '\"\"':
					propertieValue=None
				# senao remover	as aspas duplas
				else:
					propertieValue=propertieValue.strip('\"')
				# armazenar o valor na chave atual
				properties[k]=propertieValue
				# utilizar o brake para não continuar o laco
				break
	# retornar o dicionario preenchido
	return properties

# funcaoo para validar o nome de usuario utilizado
# pattern = pattern para validar o username
# username = nome do usuario
def usernameValidator(pattern,username):
	# verificar se o nome do usuario condiz com a expessao
	if not re.match(pattern,username):
		# exibir mensagemd e erro
		print "O nome de usuário '"+username+"' é inválido."
		# enviar mensagem para log
		errorLog("Nome de usuário '"+username+"' inválido.")
		#retornar codigo de erro
		exit(4) # nome de usuário inválido

if __name__ == '__main__':
	main()