#----------Python config----------------
pythonExec = '/root/miniconda2/envs/findRefrain3/bin/python' #python executeable to run async plot process

#----Temp audio file locations----------
audioOutPath = '/tmp/offlineOutput.wav' #compiled app writes to this location
audioInPath = '/tmp/offlineInput.wav' #Python writes to this location

#----------Faust config----------------
offlineCompArch = '/opt/faust/architecture/sndfile.cpp' #architecture file of compilation