/**
 * AIOX CLI Integrity Smoke Test
 *
 * Verifies the project-local CLI contract without requiring a package runner.
 *
 * @module verify-cli-integrity
 * @story 2.2 - CLI diagnostics and manifests
 */

const { spawnSync } = require('child_process');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..', '..', '..');
const cliPath = path.join(projectRoot, '.aiox-core', 'cli', 'index.js');

function runCli(args) {
  const result = spawnSync(process.execPath, [cliPath, ...args], {
    cwd: projectRoot,
    encoding: 'utf8',
    windowsHide: true,
  });

  return {
    ...result,
    output: `${result.stdout || ''}${result.stderr || ''}`,
  };
}

function assertCommand(args, predicate, description) {
  const result = runCli(args);
  if (!predicate(result)) {
    throw new Error(`${description}\n${result.output}`.trim());
  }
  return result;
}

function main() {
  const version = assertCommand(
    ['--version'],
    (result) => result.status === 0 && result.stdout.trim() === '5.4.1',
    'CLI version contract failed.',
  );

  const help = assertCommand(
    ['--help'],
    (result) => result.status === 0 && result.stdout.includes('doctor') && !result.stdout.includes('aiox install'),
    'CLI help contract failed.',
  );

  const doctor = assertCommand(
    ['doctor', '--json'],
    (result) => {
      if (result.status !== 0) return false;
      const report = JSON.parse(result.stdout);
      return report.summary && report.summary.fail === 0;
    },
    'Doctor contract failed.',
  );

  assertCommand(
    ['manifest', 'validate'],
    (result) => result.status === 0 && result.stdout.includes('All manifests valid'),
    'Manifest validation contract failed.',
  );

  assertCommand(
    ['config', 'validate'],
    (result) => result.status === 0 && result.stdout.includes('Config validation: PASS'),
    'Config validation contract failed.',
  );

  console.log(
    `AIOX CLI integrity smoke test passed (version=${version.stdout.trim()}, `
      + `doctor_failures=${JSON.parse(doctor.stdout).summary.fail}, help=registered-only).`,
  );
  void help;
}

try {
  main();
} catch (error) {
  console.error(`AIOX CLI integrity smoke test failed: ${error.message}`);
  process.exitCode = 1;
}
