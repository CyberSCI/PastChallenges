#!/bin/bash

gcc -fPIE -pie -fstack-protector main.c -o main
pwninit --bin main