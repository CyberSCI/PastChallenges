import { defineConfig } from "vitest/config";

export default defineConfig({
	test: {
		reporters: [["json", { outputFile: ".vitest/results.json" }]],
	},
});
