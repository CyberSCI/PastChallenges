#!/usr/bin/env node

import { Command } from "commander";
import { loadCommands } from "./commands/dam.js";

const program = new Command();
program
	.name("dam-builder")
	.description("A CLI tool for building dams")
	.version("0.1.0");
loadCommands(program);
program.parse(process.argv);
