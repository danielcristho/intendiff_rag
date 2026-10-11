// This loads the installed package-manager utility, never a sample module.
const fs = require('node:fs');
const semver = require('~/.nvm/versions/node/v24.21.0/lib/node_modules/npm/node_modules/semver');
const requests = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(requests.map(r => ({...r, satisfies: semver.satisfies(r.version, r.range)}))));
