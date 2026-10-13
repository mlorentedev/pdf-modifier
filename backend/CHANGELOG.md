# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.9.1](https://github.com/mlorentedev/pdf-modifier-mcp/compare/v1.9.0...v1.9.1) (2026-10-13)


### Bug Fixes

* **ai:** route to mimo-v2.6-flash, the successor to the retired mimo-v2.5 ([#178](https://github.com/mlorentedev/pdf-modifier-mcp/issues/178)) ([f3e1ad8](https://github.com/mlorentedev/pdf-modifier-mcp/commit/f3e1ad883e57a3259a59382efbb6280dcc9eb0d6))
* **harness:** port the reviewer pool and attestation to the SSOT shape (CI-001) ([#175](https://github.com/mlorentedev/pdf-modifier-mcp/issues/175)) ([b7291a1](https://github.com/mlorentedev/pdf-modifier-mcp/commit/b7291a1407b15a4a2d29b19f3ca897a55766d8b5))

## [1.9.0](https://github.com/mlorentedev/pdf-modifier-mcp/compare/v1.8.0...v1.9.0) (2026-09-22)


### Features

* add consistency reviewer for replacement targets ([#139](https://github.com/mlorentedev/pdf-modifier-mcp/issues/139)) ([7616fb0](https://github.com/mlorentedev/pdf-modifier-mcp/commit/7616fb0c677d598ea19f9735438657d3ef1680ae))
* **core:** whole-span exact match option to avoid substring collisions ([#151](https://github.com/mlorentedev/pdf-modifier-mcp/issues/151)) ([0d8e723](https://github.com/mlorentedev/pdf-modifier-mcp/commit/0d8e7232c2da996f0042bf71e146b5d1f5209de5))


### Bug Fixes

* preserve PDF background and font weight on text replacement ([#136](https://github.com/mlorentedev/pdf-modifier-mcp/issues/136)) ([1f8e947](https://github.com/mlorentedev/pdf-modifier-mcp/commit/1f8e947494e0a190edd03a7836c54a0a72e7e2de))

## [1.8.0](https://github.com/mlorentedev/pdf-modifier-mcp/compare/v1.7.1...v1.8.0) (2026-08-06)


### Features

* **web:** PDF preview — element grouping, click-to-locate, precise highlight ([#118](https://github.com/mlorentedev/pdf-modifier-mcp/issues/118)) ([#121](https://github.com/mlorentedev/pdf-modifier-mcp/issues/121)) ([e60d607](https://github.com/mlorentedev/pdf-modifier-mcp/commit/e60d6077f5ec22fe7c39b319d82f1383e8d4b3b0))


### Documentation

* **spec:** archive WEB-002 (PR [#121](https://github.com/mlorentedev/pdf-modifier-mcp/issues/121) merged) + pdf.js/grouping lesson ([#123](https://github.com/mlorentedev/pdf-modifier-mcp/issues/123)) ([e97a9be](https://github.com/mlorentedev/pdf-modifier-mcp/commit/e97a9beaac8301670ad4b089646a224d69cb4a5b))

## [1.7.1](https://github.com/mlorentedev/pdf-modifier-mcp/compare/v1.7.0...v1.7.1) (2026-06-24)


### Bug Fixes

* sync uv.lock version with pyproject.toml (1.7.0) ([#107](https://github.com/mlorentedev/pdf-modifier-mcp/issues/107)) ([e2af8d9](https://github.com/mlorentedev/pdf-modifier-mcp/commit/e2af8d936584a86de6ed9b4e823d65b689cec8fd))

## [1.7.0](https://github.com/mlorentedev/pdf-modifier-mcp/compare/v1.6.0...v1.7.0) (2026-06-24)


### Features

* **infra:** Docker multi-stage builds, compose stack, Makefile targets ([#91](https://github.com/mlorentedev/pdf-modifier-mcp/issues/91)) ([2fc84be](https://github.com/mlorentedev/pdf-modifier-mcp/commit/2fc84be248b3a89e144b094eb53c42ffe0ebceca))

## [1.6.0](https://github.com/mlorentedev/pdf-modifier-mcp/compare/v1.5.0...v1.6.0) (2026-06-24)


### Features

* **ai:** NaN Cloud AI layer with model router + throttle ([#88](https://github.com/mlorentedev/pdf-modifier-mcp/issues/88)) ([ae05deb](https://github.com/mlorentedev/pdf-modifier-mcp/commit/ae05deb36ff6cabd60c21deceaf22209705ca6f5))
* **web:** FastAPI + SvelteKit web UI for PDF editing ([#89](https://github.com/mlorentedev/pdf-modifier-mcp/issues/89)) ([e1ea0eb](https://github.com/mlorentedev/pdf-modifier-mcp/commit/e1ea0ebec48c026f51354e5e7503420e60f7380b))

## [1.5.0](https://github.com/mlorentedev/pdf-modifier-mcp/compare/v1.4.3...v1.5.0) (2026-06-21)


### Features

* **core:** custom font support with FontResolver pattern ([#86](https://github.com/mlorentedev/pdf-modifier-mcp/issues/86)) ([09e7e45](https://github.com/mlorentedev/pdf-modifier-mcp/commit/09e7e45e6af8682875d7d8190a3fdb5a203a5594)), closes [#3](https://github.com/mlorentedev/pdf-modifier-mcp/issues/3)
* **core:** page range support for targeted PDF modifications ([#84](https://github.com/mlorentedev/pdf-modifier-mcp/issues/84)) ([68e1c19](https://github.com/mlorentedev/pdf-modifier-mcp/commit/68e1c1935e2f485e2e6217a83096a62dd530d71d))

## [1.4.3](https://github.com/mlorentedev/pdf-modifier-mcp/compare/v1.4.2...v1.4.3) (2026-06-20)


### Bug Fixes

* **security:** harden .gitignore + add pre-implementation audit ([#82](https://github.com/mlorentedev/pdf-modifier-mcp/issues/82)) ([f53288c](https://github.com/mlorentedev/pdf-modifier-mcp/commit/f53288c8d57b31324c2d5e5fdfcdceee0d1bd656))


### Documentation

* architecture session — 12 ADRs, 6 specs, AGENTS.md migration ([#79](https://github.com/mlorentedev/pdf-modifier-mcp/issues/79)) ([2dd5e26](https://github.com/mlorentedev/pdf-modifier-mcp/commit/2dd5e264b6aace81b1582d9bc45a7f1a01a3191c))

## [1.4.2](https://github.com/mlorentedev/pdf-modifier-mcp/compare/v1.4.1...v1.4.2) (2026-05-29)


### Documentation

* migrate project-bound knowledge into docs/ (KPM-017) ([#63](https://github.com/mlorentedev/pdf-modifier-mcp/issues/63)) ([61a08a7](https://github.com/mlorentedev/pdf-modifier-mcp/commit/61a08a7ad0b05dda908187d3e864070023724b36))

## [1.4.1](https://github.com/mlorentedev/pdf-modifier-mcp/compare/v1.4.0...v1.4.1) (2026-03-15)


### Documentation

* update docs for v1.4 features ([#59](https://github.com/mlorentedev/pdf-modifier-mcp/issues/59)) ([4b10f11](https://github.com/mlorentedev/pdf-modifier-mcp/commit/4b10f11d3e7a6fe258ca05bd7a0e5958f5c1d3db))

## [1.4.0](https://github.com/mlorentedev/pdf-modifier-mcp/compare/v1.3.0...v1.4.0) (2026-03-15)


### Features

* add file size validation to prevent OOM with large PDFs ([#54](https://github.com/mlorentedev/pdf-modifier-mcp/issues/54)) ([d289274](https://github.com/mlorentedev/pdf-modifier-mcp/commit/d28927409e5a1e6a34d7ae4e33aae1493b8c53de))
* **core:** implement multi-span regex matching ([#57](https://github.com/mlorentedev/pdf-modifier-mcp/issues/57)) ([ad56a05](https://github.com/mlorentedev/pdf-modifier-mcp/commit/ad56a05ccbd02ef68edd9beebf9dc752b1e77512)), closes [#4](https://github.com/mlorentedev/pdf-modifier-mcp/issues/4)
* **mcp:** add batch processing support ([#56](https://github.com/mlorentedev/pdf-modifier-mcp/issues/56)) ([fb24f32](https://github.com/mlorentedev/pdf-modifier-mcp/commit/fb24f32f65405d0bb3c3bc3edae9191803e3ca3e)), closes [#11](https://github.com/mlorentedev/pdf-modifier-mcp/issues/11)


### Bug Fixes

* **ci:** auto-trigger CI on release-please PR branch ([#58](https://github.com/mlorentedev/pdf-modifier-mcp/issues/58)) ([ef7e73a](https://github.com/mlorentedev/pdf-modifier-mcp/commit/ef7e73a87f099e0697ea178b4c4165fbd602f519))

## [1.3.0](https://github.com/mlorentedev/pdf-modifier-mcp/compare/v1.2.0...v1.3.0) (2026-03-14)


### Features

* **analyzer:** add hyperlink inventory support ([#41](https://github.com/mlorentedev/pdf-modifier-mcp/issues/41)) ([b072402](https://github.com/mlorentedev/pdf-modifier-mcp/commit/b07240234e96491392694964e9029ce090164aea))
* **security:** add password protection support and structured json logging ([#35](https://github.com/mlorentedev/pdf-modifier-mcp/issues/35)) ([fbab7bf](https://github.com/mlorentedev/pdf-modifier-mcp/commit/fbab7bffd9be5c3fb891b7cc2072898e71a46479))
* test semantic release workflow ([aa7158e](https://github.com/mlorentedev/pdf-modifier-mcp/commit/aa7158e46ba679195efaab5c43659cc4cb367567))


### Bug Fixes

* **ci:** bypass branch protection by pushing tags manually and using --no-push ([#45](https://github.com/mlorentedev/pdf-modifier-mcp/issues/45)) ([d398e1b](https://github.com/mlorentedev/pdf-modifier-mcp/commit/d398e1ba8b0bf4ac706bb810ef393c7a66632d40))
* **ci:** correct YAML syntax error in release workflow ([#46](https://github.com/mlorentedev/pdf-modifier-mcp/issues/46)) ([1014c2a](https://github.com/mlorentedev/pdf-modifier-mcp/commit/1014c2a0da327d593e931c5109b6d981d54cdb78))
* **ci:** disable branch push during release to bypass strict protection ([#44](https://github.com/mlorentedev/pdf-modifier-mcp/issues/44)) ([ca35911](https://github.com/mlorentedev/pdf-modifier-mcp/commit/ca35911fd912db6a2974ed0805b9f1a8a86a6262))
* **ci:** enable ci on all branches and remove redundant release valid… ([2b9170a](https://github.com/mlorentedev/pdf-modifier-mcp/commit/2b9170a6cf0239d6f47fe745811284ee1988460e))
* **ci:** enable ci on all branches and remove redundant release validation ([ebb662e](https://github.com/mlorentedev/pdf-modifier-mcp/commit/ebb662ed0192194f4eece80373c51a2405146aa4))
* **ci:** ensure publish-mcp job checks out the actual released tag ([#37](https://github.com/mlorentedev/pdf-modifier-mcp/issues/37)) ([b8099d5](https://github.com/mlorentedev/pdf-modifier-mcp/commit/b8099d58dbccfafd51314a8b4929bb10bb7faf2f))
* **ci:** fetch full history to fix semantic-release detached head error ([395106f](https://github.com/mlorentedev/pdf-modifier-mcp/commit/395106f5adbddf0ec4c458f2ebec55d7c591c442))
* **ci:** improve new release detection in release workflow ([#36](https://github.com/mlorentedev/pdf-modifier-mcp/issues/36)) ([0dd63b0](https://github.com/mlorentedev/pdf-modifier-mcp/commit/0dd63b09044c90fdde7c33bfe45adfb4acec757a))
* **ci:** only publish to PyPI when dist artifacts exist ([#33](https://github.com/mlorentedev/pdf-modifier-mcp/issues/33)) ([81e14eb](https://github.com/mlorentedev/pdf-modifier-mcp/commit/81e14ebb1955c3413a2d105a0e17d5919b6976ea))
* **ci:** repair yaml syntax error in ci workflow ([0b03ce2](https://github.com/mlorentedev/pdf-modifier-mcp/commit/0b03ce2e0b896a30a22dabddf7060c32a13060aa))
* **ci:** replace docker action with native python semantic-release workflow ([c4dc483](https://github.com/mlorentedev/pdf-modifier-mcp/commit/c4dc48371f4c7a520dd2fd4bd50992922dc40c86))
* **ci:** revert to RELEASE_TOKEN to bypass branch protection ([#39](https://github.com/mlorentedev/pdf-modifier-mcp/issues/39)) ([5e1f9a7](https://github.com/mlorentedev/pdf-modifier-mcp/commit/5e1f9a7156ae57cd66f64831eca403f4394b79b2))
* **ci:** robust release detection and fix token usage ([#38](https://github.com/mlorentedev/pdf-modifier-mcp/issues/38)) ([849730f](https://github.com/mlorentedev/pdf-modifier-mcp/commit/849730f820adbf051d80fad6ecdd3005d2db2e34))
* **ci:** trigger release on push to master for robustness ([2604a10](https://github.com/mlorentedev/pdf-modifier-mcp/commit/2604a108c40ea50d9f14a0c02df4cc3836e0fb8b))
* **ci:** use trusted pypi publisher action ([4652568](https://github.com/mlorentedev/pdf-modifier-mcp/commit/46525688c4161f4a4de3e2996f9f5eae1acfde6d))
* **cli:** improve hyperlink counter visibility ([#42](https://github.com/mlorentedev/pdf-modifier-mcp/issues/42)) ([8549509](https://github.com/mlorentedev/pdf-modifier-mcp/commit/85495094e2180fdb08dff4a28866607ebcbb1d5d))
* **release:** avoid protected branch push issue ([#28](https://github.com/mlorentedev/pdf-modifier-mcp/issues/28)) ([f42799e](https://github.com/mlorentedev/pdf-modifier-mcp/commit/f42799e782ebcef0a179b1aa93da269f7b024f05))
* **release:** correct changelog template for semantic-release v9 ([#27](https://github.com/mlorentedev/pdf-modifier-mcp/issues/27)) ([7439740](https://github.com/mlorentedev/pdf-modifier-mcp/commit/7439740ae12df8f2154798f638bc29c5d9561171))
* **release:** disable internal pypi upload in semantic-release config ([4149d89](https://github.com/mlorentedev/pdf-modifier-mcp/commit/4149d892437e1b0d4bb851a3ac577d63eb41802a))
* **release:** remove problematic remote type config ([827a5ef](https://github.com/mlorentedev/pdf-modifier-mcp/commit/827a5ef555bbbeb5240fa2ef1ce374d002e402cb))
* **release:** remove problematic remote type config ([f9a44f9](https://github.com/mlorentedev/pdf-modifier-mcp/commit/f9a44f94345e58bcba81f13cd49968cb9a24faf7))
* **release:** remove remote config entirely to fix CI error ([0985808](https://github.com/mlorentedev/pdf-modifier-mcp/commit/0985808ae667eb7fb0c97b46d8b21721ab990dad))
* **release:** update semantic-release config for v9 compatibility ([#26](https://github.com/mlorentedev/pdf-modifier-mcp/issues/26)) ([3100eae](https://github.com/mlorentedev/pdf-modifier-mcp/commit/3100eae3b6e30bf5fafa1440de642492ec621564))
* **release:** update semantic-release config to v9 standards ([6f05422](https://github.com/mlorentedev/pdf-modifier-mcp/commit/6f05422d4e75ac20b04ec56bdcb8d9d53a2078aa))
* **release:** update semantic-release config to v9 standards ([82f313e](https://github.com/mlorentedev/pdf-modifier-mcp/commit/82f313e0be7ddc3545843f5c1cf9f92ab54f076c))
* **release:** use PAT token in checkout for git push ([#30](https://github.com/mlorentedev/pdf-modifier-mcp/issues/30)) ([ce839c5](https://github.com/mlorentedev/pdf-modifier-mcp/commit/ce839c542f91e2a8e15641a8a3737495c1a4192b))
* **release:** use RELEASE_TOKEN PAT to bypass branch protection ([#29](https://github.com/mlorentedev/pdf-modifier-mcp/issues/29)) ([0af8e9e](https://github.com/mlorentedev/pdf-modifier-mcp/commit/0af8e9e0e745179f2258b70987bd7957a4ac8a97))
* remove unsupported description argument from FastMCP ([cfe1225](https://github.com/mlorentedev/pdf-modifier-mcp/commit/cfe12255b55d7c19ad131e6ec4ff2784e6cc346e))
* resolve TypeError in FastMCP initialization ([879e712](https://github.com/mlorentedev/pdf-modifier-mcp/commit/879e712ca29f22c413060d90dbf8491008a1d1b4))
* **site:** improve UI contrast and accessible colors ([#49](https://github.com/mlorentedev/pdf-modifier-mcp/issues/49)) ([38c8e27](https://github.com/mlorentedev/pdf-modifier-mcp/commit/38c8e2722cc85ed63469a6b10f09cf47633d668d))
* **smithery:** remove .well-known folder (for HTTP servers only) ([#34](https://github.com/mlorentedev/pdf-modifier-mcp/issues/34)) ([29cb390](https://github.com/mlorentedev/pdf-modifier-mcp/commit/29cb39054601cc9140dd4078c76a14244ff85726))
* **smithery:** use uvx to run package from PyPI ([#32](https://github.com/mlorentedev/pdf-modifier-mcp/issues/32)) ([dffb565](https://github.com/mlorentedev/pdf-modifier-mcp/commit/dffb56587b903246d219eefac3926be6119e35df))


### Documentation

* add smithery server card for discovery ([dfa30d3](https://github.com/mlorentedev/pdf-modifier-mcp/commit/dfa30d39c153fedb30baaeb5a8785b9ff6672655))
* add Starlight documentation site with GitHub Pages deployment ([d4e00a0](https://github.com/mlorentedev/pdf-modifier-mcp/commit/d4e00a03325c9a8ef6f3f1837ec0003dfa0f5ffc))
* finalize readme with latest tools and stack info ([#50](https://github.com/mlorentedev/pdf-modifier-mcp/issues/50)) ([b5aad8a](https://github.com/mlorentedev/pdf-modifier-mcp/commit/b5aad8ac60ab7b3c0dca2fa3db2388ef0a7b2a6c))
* **site:** add branding, badges, favicon, and improved content ([237b166](https://github.com/mlorentedev/pdf-modifier-mcp/commit/237b166171cd024e0e6c4c1bd5cea71e5b83554d))

## [1.2.0](https://github.com/mlorentedev/pdf-modifier-mcp/compare/v1.1.1...v1.2.0) (2026-03-14)


### Features

* **analyzer:** add hyperlink inventory support ([#41](https://github.com/mlorentedev/pdf-modifier-mcp/issues/41)) ([b072402](https://github.com/mlorentedev/pdf-modifier-mcp/commit/b07240234e96491392694964e9029ce090164aea))


### Bug Fixes

* **ci:** bypass branch protection by pushing tags manually and using --no-push ([#45](https://github.com/mlorentedev/pdf-modifier-mcp/issues/45)) ([d398e1b](https://github.com/mlorentedev/pdf-modifier-mcp/commit/d398e1ba8b0bf4ac706bb810ef393c7a66632d40))
* **ci:** correct YAML syntax error in release workflow ([#46](https://github.com/mlorentedev/pdf-modifier-mcp/issues/46)) ([1014c2a](https://github.com/mlorentedev/pdf-modifier-mcp/commit/1014c2a0da327d593e931c5109b6d981d54cdb78))
* **ci:** disable branch push during release to bypass strict protection ([#44](https://github.com/mlorentedev/pdf-modifier-mcp/issues/44)) ([ca35911](https://github.com/mlorentedev/pdf-modifier-mcp/commit/ca35911fd912db6a2974ed0805b9f1a8a86a6262))
* **ci:** ensure publish-mcp job checks out the actual released tag ([#37](https://github.com/mlorentedev/pdf-modifier-mcp/issues/37)) ([b8099d5](https://github.com/mlorentedev/pdf-modifier-mcp/commit/b8099d58dbccfafd51314a8b4929bb10bb7faf2f))
* **ci:** revert to RELEASE_TOKEN to bypass branch protection ([#39](https://github.com/mlorentedev/pdf-modifier-mcp/issues/39)) ([5e1f9a7](https://github.com/mlorentedev/pdf-modifier-mcp/commit/5e1f9a7156ae57cd66f64831eca403f4394b79b2))
* **ci:** robust release detection and fix token usage ([#38](https://github.com/mlorentedev/pdf-modifier-mcp/issues/38)) ([849730f](https://github.com/mlorentedev/pdf-modifier-mcp/commit/849730f820adbf051d80fad6ecdd3005d2db2e34))
* **cli:** improve hyperlink counter visibility ([#42](https://github.com/mlorentedev/pdf-modifier-mcp/issues/42)) ([8549509](https://github.com/mlorentedev/pdf-modifier-mcp/commit/85495094e2180fdb08dff4a28866607ebcbb1d5d))
* **site:** improve UI contrast and accessible colors ([#49](https://github.com/mlorentedev/pdf-modifier-mcp/issues/49)) ([38c8e27](https://github.com/mlorentedev/pdf-modifier-mcp/commit/38c8e2722cc85ed63469a6b10f09cf47633d668d))


### Documentation

* finalize readme with latest tools and stack info ([#50](https://github.com/mlorentedev/pdf-modifier-mcp/issues/50)) ([b5aad8a](https://github.com/mlorentedev/pdf-modifier-mcp/commit/b5aad8ac60ab7b3c0dca2fa3db2388ef0a7b2a6c))

## [v1.1.1](https://github.com/mlorentedev/pdf-modifier-mcp/releases/tag/v1.1.1) (2026-03-08)



### Bug fixes


- improve new release detection in release workflow ([`0dd63b0`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/0dd63b09044c90fdde7c33bfe45adfb4acec757a))





### Chores


- sync server.json to v1.1.0 and conditionalize mcp publishing ([`f297411`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/f2974117a6266c981b95aae89b746b5ac072c3e4))

- fix mcp ownership comment position in README for registry validation ([`c20f5a4`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/c20f5a4f88bbc386a54df0685768f1e0b89ecc42))





## [v1.1.0](https://github.com/mlorentedev/pdf-modifier-mcp/releases/tag/v1.1.0) (2026-03-08)



### Chores


- fix semantic-release version_variables syntax for server.json ([`877325c`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/877325c0c35041da148531ebb6fa07711a268c74))

- standardize mcp distribution and harden core ([`e7fe913`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/e7fe9134b7e714641955f7a3335fd8efa4d7b77a))





### Documentation


- add branding, badges, favicon, and improved content ([`237b166`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/237b166171cd024e0e6c4c1bd5cea71e5b83554d))

- add Starlight documentation site with GitHub Pages deployment ([`d4e00a0`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/d4e00a03325c9a8ef6f3f1837ec0003dfa0f5ffc))





### Features


- add password protection support and structured json logging ([`fbab7bf`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/fbab7bffd9be5c3fb891b7cc2072898e71a46479))







## [v1.0.3](https://github.com/mlorentedev/pdf-modifier-mcp/releases/tag/v1.0.3) (2026-01-15)



### Bug fixes


- remove .well-known folder (for HTTP servers only) ([`29cb390`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/29cb39054601cc9140dd4078c76a14244ff85726))





## [v1.0.2](https://github.com/mlorentedev/pdf-modifier-mcp/releases/tag/v1.0.2) (2026-01-15)



### Bug fixes


- only publish to PyPI when dist artifacts exist ([`81e14eb`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/81e14ebb1955c3413a2d105a0e17d5919b6976ea))





## [v1.0.1](https://github.com/mlorentedev/pdf-modifier-mcp/releases/tag/v1.0.1) (2026-01-15)



### Bug fixes


- use uvx to run package from PyPI ([`dffb565`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/dffb56587b903246d219eefac3926be6119e35df))





### Refactoring


- simplify release workflow and fix deprecation warning ([`4fe922c`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/4fe922c74529186da9ac1a8b8fe2844dd512995c))





## [v1.0.0](https://github.com/mlorentedev/pdf-modifier-mcp/releases/tag/v1.0.0) (2026-01-15)



### Bug fixes


- use PAT token in checkout for git push ([`ce839c5`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/ce839c542f91e2a8e15641a8a3737495c1a4192b))

- use RELEASE_TOKEN PAT to bypass branch protection ([`ce839c5`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/ce839c542f91e2a8e15641a8a3737495c1a4192b))

- use RELEASE_TOKEN in checkout for git push auth ([`ce839c5`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/ce839c542f91e2a8e15641a8a3737495c1a4192b))

- use RELEASE_TOKEN PAT to bypass branch protection ([`0af8e9e`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/0af8e9e0e745179f2258b70987bd7957a4ac8a97))

- avoid protected branch push issue ([`f42799e`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/f42799e782ebcef0a179b1aa93da269f7b024f05))

- update semantic-release config for v9 compatibility ([`f42799e`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/f42799e782ebcef0a179b1aa93da269f7b024f05))

- correct changelog template syntax for semantic-release v9 ([`f42799e`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/f42799e782ebcef0a179b1aa93da269f7b024f05))

- use --no-push --no-commit to avoid protected branch issue ([`f42799e`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/f42799e782ebcef0a179b1aa93da269f7b024f05))

- correct changelog template for semantic-release v9 ([`7439740`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/7439740ae12df8f2154798f638bc29c5d9561171))

- update semantic-release config for v9 compatibility ([`7439740`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/7439740ae12df8f2154798f638bc29c5d9561171))

- correct changelog template syntax for semantic-release v9 ([`7439740`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/7439740ae12df8f2154798f638bc29c5d9561171))

- update semantic-release config for v9 compatibility ([`3100eae`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/3100eae3b6e30bf5fafa1440de642492ec621564))

- disable internal pypi upload in semantic-release config ([`4149d89`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/4149d892437e1b0d4bb851a3ac577d63eb41802a))

- use trusted pypi publisher action ([`4652568`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/46525688c4161f4a4de3e2996f9f5eae1acfde6d))

- replace docker action with native python semantic-release workflow ([`c4dc483`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/c4dc48371f4c7a520dd2fd4bd50992922dc40c86))

- fetch full history to fix semantic-release detached head error ([`395106f`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/395106f5adbddf0ec4c458f2ebec55d7c591c442))

- repair yaml syntax error in ci workflow ([`0b03ce2`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/0b03ce2e0b896a30a22dabddf7060c32a13060aa))

- remove remote config entirely to fix CI error ([`0985808`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/0985808ae667eb7fb0c97b46d8b21721ab990dad))

- trigger release on push to master for robustness ([`2604a10`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/2604a108c40ea50d9f14a0c02df4cc3836e0fb8b))

- remove problematic remote type config ([`f9a44f9`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/f9a44f94345e58bcba81f13cd49968cb9a24faf7))

- update semantic-release config to v9 standards ([`82f313e`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/82f313e0be7ddc3545843f5c1cf9f92ab54f076c))

- enable ci on all branches and remove redundant release validation ([`ebb662e`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/ebb662ed0192194f4eece80373c51a2405146aa4))

- remove unsupported description argument from FastMCP ([`cfe1225`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/cfe12255b55d7c19ad131e6ec4ff2784e6cc346e))





### Continuous integration


- reduce python matrix to min (3.10) and max (3.12) versions ([`6d23ad7`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/6d23ad7b9f9cc649e9189755752ce8914b8f88d4))

- switch to official python-semantic-release action for stability ([`fad8a7c`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/fad8a7c307714f03c0cc39d84faa7e1f32d38f03))

- remove release verification step to avoid detached head errors ([`fba23a8`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/fba23a818e5f01a84bed6d1183027fc630b13127))

- add semantic-release config verification to CI pipeline ([`4f2ea0d`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/4f2ea0dce42d286548539872b7d68b71fe8d32aa))

- test release workflow on feature branch ([`1f1dc85`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/1f1dc85f2924b83969c2736ed7c2c75ceb9ddc69))





### Documentation


- add smithery server card for discovery ([`dfa30d3`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/dfa30d39c153fedb30baaeb5a8785b9ff6672655))





### Features


- test semantic release workflow ([`aa7158e`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/aa7158e46ba679195efaab5c43659cc4cb367567))





### Refactoring


- switch to tag-based release workflow (removes semantic-release) ([`edd0892`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/edd08926adfa754bb107dcfedbae8229e2928983))

- modernize project structure and update CI/CD ([`e024b0e`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/e024b0e3af890f55457f15881c8fc9a2956221ea))
