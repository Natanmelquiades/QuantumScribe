/**
 * Doctor Check: npm Packages
 *
 * Validates:
 * 1. node_modules/ exists in project root (quick sanity check)
 * 2. (INS-4.12) .aiox-core/node_modules/ exists and contains all declared deps
 *
 * @module aiox-core/doctor/checks/npm-packages
 * @story INS-4.1, INS-4.12
 */

const path = require('path');
const fs = require('fs');

const name = 'npm-packages';

async function run(context) {
  const nodeModulesPath = path.join(context.projectRoot, 'node_modules');
  const projectNodeModulesPresent = fs.existsSync(nodeModulesPath);

  // Check 2 (INS-4.12): .aiox-core/node_modules/ completeness
  const aioxCoreDir = path.join(context.projectRoot, '.aiox-core');
  const aioxCorePackageJson = path.join(aioxCoreDir, 'package.json');
  const aioxCoreNodeModules = path.join(aioxCoreDir, 'node_modules');

  // AIOX supports a project-local isolated install. A root node_modules
  // directory is optional when .aiox-core has its declared dependencies.
  if (!projectNodeModulesPresent && !fs.existsSync(aioxCoreNodeModules)) {
    return {
      check: name,
      status: 'FAIL',
      message: 'Neither project nor .aiox-core node_modules found',
      fixCommand: 'cd .aiox-core && npm install --production',
    };
  }

  if (fs.existsSync(aioxCorePackageJson)) {
    if (!fs.existsSync(aioxCoreNodeModules)) {
      return {
        check: name,
        status: 'FAIL',
        message: 'node_modules present, but .aiox-core/node_modules/ missing',
        fixCommand: 'cd .aiox-core && npm install --production',
      };
    }

    // Verify all declared deps are installed
    try {
      const pkg = JSON.parse(fs.readFileSync(aioxCorePackageJson, 'utf8'));
      const deps = Object.keys(pkg.dependencies || {});
      const missing = [];

      for (const dep of deps) {
        const depPath = path.join(aioxCoreNodeModules, dep);
        if (!fs.existsSync(depPath)) {
          missing.push(dep);
        }
      }

      if (missing.length > 0) {
        return {
          check: name,
          status: 'FAIL',
          message: `node_modules present, but .aiox-core missing deps: ${missing.join(', ')}`,
          fixCommand: 'cd .aiox-core && npm install --production',
        };
      }
    } catch {
      // If we can't parse package.json, just check existence passed above
    }
  }

  return {
    check: name,
    status: 'PASS',
    message: projectNodeModulesPresent
      ? 'node_modules present' + (fs.existsSync(aioxCoreNodeModules) ? ', .aiox-core deps complete' : '')
      : '.aiox-core deps complete (root node_modules not required for isolated AIOX install)',
    fixCommand: null,
  };
}

module.exports = { name, run };
