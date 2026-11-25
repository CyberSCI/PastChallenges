import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
	commandLine,
	extendMatchers,
	type ScratchDirectory,
	scratchDirectory,
} from "vitest-command-line";

extendMatchers();

describe("dam-builder", () => {
	const cli = commandLine({
		command: ["node", "./dist/cli.js"],
		name: "dam-builder",
		env: { FORCE_COLOR: "0" },
	});
	let directory: ScratchDirectory;

	beforeEach(async () => {
		directory = scratchDirectory();
		await directory.create();
	});

	afterEach(async () => {
		await directory.remove();
	});

	it("correctly accounts for the number of beavers", async () => {
		const result = await cli.run(["plan", "--beavers", "5"], {
			timeout: 5_000,
			subprocessCleanup: "process-tree",
		});

		expect(result).toSucceed();
		expect(result).toHaveStdout(/planning a dam for 5 beavers.../i);
	});
});
