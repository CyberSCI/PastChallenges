# CyberSci Regionals 2025/26
#
# Dmitriy Beryoza (0xd13a@gmail.com)
#
# Water treatment challenge

default: wt.exe

%.o: %.c
	export INCLUDE=./ow/h
	./ow/binl/wcc -bt=dos -bc -q -ms $< 

wt.exe: water-treatment.o
	export LIB=./ow/lib286:./ow/lib286/dos
	./ow/binl/wlink op quiet format dos name $@ file $< 
