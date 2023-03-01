import json, logging, subprocess, os

ROOT = "/workspace/project/"

def exists(path:str):
	return os.path.exists(path)

def read_json(path:str):
	with open(path) as f:
		return json.load(f)

def write_json(path:str, content:dict):
	with open(path, "w+") as file:
		json.dump(content, file, indent=4)

def write_txt(path:str, content:str):
	if exists(path):
		with open(path, 'a+') as f:
			f.write(str(content)+'\n') 
	else:
		with open(path, 'w+') as f:
			f.write(str(content)+'\n')

def read_txt(path:str):
	with open(path) as f:
		return f.read()
	
def cmd(command, split_action=True):
	COLOR_ERR = ["0m", "1m[", "32m", "33m", "33;1m", "34m", "35m", "36m", "37m", "42m", "m]", "34;49m"]
	if split_action:
		logging.info(command.split())
		process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
	else:
		logging.info(command)
		process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell=True)

	for line in iter(process.stdout.readline,b''):
		line = line.rstrip().decode('ascii',errors='ignore')
		if line.isspace(): 
			continue
		else:
			# print(line)
			if "[" in line:
				line = "{}".format(line.split("[")[1:])
				for str in COLOR_ERR:
					line = line.replace(str, "")
			logging.info(line)
			# if not subprocess.Popen.poll(process) is None:
			#     process.returncode
			#     break