#!/bin/bash

# BUILD SCRIPT:

echo "building fishing-game..."

FLAG_STR_REDACTED="flag-REDACTED"
FLAG_STR="CyberSci{D0nt_t4k3_th3_ba1t_72ab2e}"

INITCWD=$pwd
WORKDIR="/home/crazy/Desktop/idle-froggo-fishing/IdleFroggoFishing"

rm -rf fishing_game/

mkdir -p fishing_game

mkdir -p fishing_game/stage
mkdir -p fishing_game/dist

mkdir -p fishing_game/stage/dist

cp Dockerfile fishing_game/stage/

cd Desktop/idle-froggo-fishing/IdleFroggoFishing/

rm -f IdleFroggoFishing.exe
rm -f IdleFroggoFishing.love

sed -i 's/$FLAG_STR_REDACTED/$FLAG_STR/g' main.lua

zip -9 -r IdleFroggoFishing.love .

ls

cd $INITCWD

cp $WORKDIR/IdleFroggoFishing.love fishing_game/stage/dist

cp dist/* fishing_game/stage/dist

cd fishing_game/stage/dist

cat love.exe IdleFroggoFishing.love > IdleFroggoFishing.exe

rm IdleFroggoFishing.love

cd ../

zip -r dist.zip dist/

rm -rf dist/

cd ../

zip -r stage.zip stage/

cd $WORKDIR

sed -i 's/$FLAG_STR/$FLAG_STR_REDACTED/g' main.lua

rm -f IdleFroggoFishing.love

zip -9 -r IdleFroggoFishing.love .

cd $INITCWD

cp $WORKDIR/IdleFroggoFishing.love fishing_game/dist/
cp dist/* fishing_game/dist/

cd fishing_game/dist/

cat love.exe IdleFroggoFishing.love > IdleFroggoFishing.exe

rm IdleFroggoFishing.love

cd ../

zip -r dist.zip dist/

echo "done!"




