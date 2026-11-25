import type { Command } from "commander";

export function loadCommands(program: Command) {
	program
		.command("plan")
		.option("-n, --beavers <beavers>", "Number of beavers", "1")
		.description("Plans a dam for the given number of beavers")
		.action(function () {
			const beavers = this.opts().beavers;
			console.log(`Planning a dam for ${beavers} beavers...`);
		});
}
