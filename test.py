import os
import sys
#运行目录
CurrentPath = os.getcwd()
print (CurrentPath)
#当前脚本目录
print ("##################################################")
print (os.path)
print (sys.argv[0])
print (os.path.split( os.path.realpath( sys.argv[0] ) ))
print ("##################################################")
ScriptPath = os.path.split( os.path.realpath( sys.argv[0] ) )[0]
print (ScriptPath)