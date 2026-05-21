#!/usr/bin/env node
const { spawnSync } = require('child_process')
const path = require('path')

const sub = process.argv[2] || 'install'
if (sub === 'install') {
  require('./install.js')
  process.exit(0)
}

console.log(`Usage:
  npx deepreflect-chat-history-roast-skill install
  npm run install-skill   (inside skills/chat-history-roast)
`)
process.exit(sub === 'help' ? 0 : 1)
