/**
 * Doctor Command
 *
 * Exposes the existing AIOX Doctor checks through the project-local CLI.
 *
 * @module cli/commands/doctor
 * @story 2.2 - CLI diagnostics and manifests
 */

const { Command } = require('commander');
const { runDoctorChecks } = require('../../../core/doctor');

async function doctorAction(options) {
  try {
    const result = await runDoctorChecks({
      fix: Boolean(options.fix),
      json: Boolean(options.json),
      dryRun: Boolean(options.dryRun),
      quiet: Boolean(options.quiet),
    });

    process.stdout.write(`${result.formatted.trimEnd()}\n`);

    if (result.data?.summary?.fail > 0) {
      process.exitCode = 1;
    }
  } catch (error) {
    console.error(`Doctor failed: ${error.message}`);
    process.exitCode = 1;
  }
}

function createDoctorCommand() {
  return new Command('doctor')
    .description('Run system diagnostics')
    .option('--json', 'Print structured JSON output')
    .option('--fix', 'Apply available automatic fixes')
    .option('--dry-run', 'Preview available fixes without changing files')
    .option('-q, --quiet', 'Reduce human-readable output')
    .action(doctorAction);
}

module.exports = {
  createDoctorCommand,
};
