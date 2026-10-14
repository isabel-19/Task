// Local, read-only adapter for the preloaded npm tarball cache. No internet requests.
const http = require('node:http')
const zlib = require('node:zlib')
const cacache = require('C:/Program Files/nodejs/node_modules/npm/node_modules/cacache')
const cache = process.argv[2]
const prefix = 'make-fetch-happen:request-cache:https://registry.npmjs.org/'
const manifests = new Map()
const tarballs = new Map()
function packageJson(buffer) {
  const data = zlib.gunzipSync(buffer)
  let offset = 0
  while (offset + 512 < data.length) {
    const name = data.subarray(offset, offset + 100).toString().replace(/\0.*$/, '')
    const size = parseInt(data.subarray(offset + 124, offset + 136).toString().replace(/\0.*$/, '').trim(), 8) || 0
    if (name.endsWith('/package.json') && name.split('/').length === 2) return JSON.parse(data.subarray(offset + 512, offset + 512 + size))
    offset += 512 + Math.ceil(size / 512) * 512
  }
}
async function start() {
  const entries = await cacache.ls(cache)
  for (const key of Object.keys(entries)) {
    if (!key.startsWith(prefix) || !key.endsWith('.tgz')) continue
    try {
      const { data, integrity } = await cacache.get(cache, key)
      const pkg = packageJson(data)
      if (!pkg) continue
      const path = key.slice(prefix.length)
      tarballs.set('/' + path, data)
      if (!manifests.has(pkg.name)) manifests.set(pkg.name, { name: pkg.name, versions: {}, 'dist-tags': {} })
      const manifest = manifests.get(pkg.name)
      pkg.dist = { tarball: 'http://127.0.0.1:4873/' + path, integrity }
      manifest.versions[pkg.version] = pkg
      manifest['dist-tags'].latest = pkg.version
    } catch (_) { /* Ignore unrelated or incomplete cached archives. */ }
  }
  http.createServer((req, res) => {
    const path = decodeURIComponent(req.url.split('?')[0])
    const data = tarballs.get(path)
    if (data) { res.writeHead(200, { 'Content-Type': 'application/octet-stream' }); return res.end(data) }
    const manifest = manifests.get(path.slice(1))
    res.writeHead(manifest ? 200 : 404, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify(manifest || { error: 'Not in preloaded cache', name: path.slice(1) }))
  }).listen(4873, '127.0.0.1', () => console.log(`Offline registry: ${manifests.size} packages at http://127.0.0.1:4873`))
}
start().catch(err => { console.error(err.message); process.exit(1) })
