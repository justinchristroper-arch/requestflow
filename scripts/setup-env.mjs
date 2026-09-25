import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { randomBytes } from 'node:crypto'
import { fileURLToPath } from 'node:url'

const root = new URL('../', import.meta.url)
const envPath = new URL('.env', root)
let content = readFileSync(existsSync(envPath) ? envPath : new URL('.env.example', root), 'utf8')
const existing = content.match(/^JWT_SECRET=(.*)$/m)
if (!existing) content += `\nJWT_SECRET=${randomBytes(48).toString('base64')}\n`
else if (!existing[1].trim() || existing[1].startsWith('replace-')) {
  content = content.replace(/^JWT_SECRET=.*$/m, `JWT_SECRET=${randomBytes(48).toString('base64')}`)
}
if (!content.endsWith('\n')) content += '\n'
for (const [key, value] of [['JWT_ALGORITHM', 'HS256'], ['ACCESS_TOKEN_EXPIRE_MINUTES', '30']]) {
  if (!new RegExp(`^${key}=`, 'm').test(content)) content += `${key}=${value}\n`
}
writeFileSync(envPath, content)
const frontendEnv = new URL('frontend/.env', root)
if (!existsSync(frontendEnv)) writeFileSync(frontendEnv, readFileSync(new URL('frontend/.env.example', root)))
console.log(`Local configuration ready in ${fileURLToPath(root)}. Existing settings preserved; secrets not displayed.`)
