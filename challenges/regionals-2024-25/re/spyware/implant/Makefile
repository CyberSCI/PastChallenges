# CyberSci Regionals 2024/25
#
# Spyware challenge by 0xd13a

OBJECTS = implant.o
IMAGES = 0.bin 1.bin 2.bin 3.bin 4.bin 5.bin 6.bin 7.bin 8.bin 9.bin a.bin b.bin c.bin d.bin e.bin f.bin

default: cat

%.bin: ../images/%.jpg
	ld -r -b binary $< -o $@

%.o: %.c
	gcc $(FLAGS) -c $< -o $@

cat: $(OBJECTS) $(IMAGES)
	gcc -s $(OBJECTS) $(IMAGES) -o $@ -lcurl -lssl -lcrypto
	upx -q --no-progress $@
