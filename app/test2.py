from Node import Cmd


cmd = Cmd("ps aux |grep ok")
cmd()
print(cmd)