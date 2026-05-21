#!/usr/bin/env node
/**
 * Copy this skill into the project's .cursor/skills/ folder (Cursor Agent Skills).
 */
const fs = require('fs')
const path = require('path')

const SKILL_DIR_NAME = 'chat-history-roast'
const SKILL_ROOT = path.join(__dirname, '..')
const COPY_NAMES = ['SKILL.md', 'README.md', 'README.zh.md', 'recipes', 'examples', 'scripts']

function findProjectRoot(start) {
  let dir = start
  for (let i = 0; i < 12; i++) {
    const cursor = path.join(dir, '.cursor')
    const git = path.join(dir, '.git')
    if (fs.existsSync(cursor) || fs.existsSync(git)) return dir
    const parent = path.dirname(dir)
    if (parent === dir) break
    dir = parent
  }
  return start
}

function copyEntry(src, dest) {
  const stat = fs.statSync(src)
  if (stat.isDirectory()) {
    fs.mkdirSync(dest, { recursive: true })
    for (const name of fs.readdirSync(src)) {
      if (name === 'node_modules' || name === 'package.json' || name === 'package-lock.json') continue
      copyEntry(path.join(src, name), path.join(dest, name))
    }
    return
  }
  fs.mkdirSync(path.dirname(dest), { recursive: true })
  fs.copyFileSync(src, dest)
}

function installTo(targetRoot) {
  const dest = path.join(targetRoot, '.cursor', 'skills', SKILL_DIR_NAME)
  fs.mkdirSync(dest, { recursive: true })
  for (const name of COPY_NAMES) {
    const src = path.join(SKILL_ROOT, name)
    if (!fs.existsSync(src)) continue
    copyEntry(src, path.join(dest, name))
  }
  return dest
}

const projectRoot = findProjectRoot(process.cwd())
const dest = installTo(projectRoot)
console.log(`[chat-history-roast] Installed Cursor skill → ${dest}`)
