# Frontend paket denetimi

5 Kasım 2026. Başlangıçtaki 37 npm kaydı aşağıda ayrı ayrı listelenmiştir. Bir satır doğrudan duyuru veya npm’in etkilenen bağımlılık zinciri kaydı olabilir.

Eski Create React App ağacı Vite/Vitest ile değiştirildi. Tailwind 3 korundu ve PostCSS, Autoprefixer ve Tailwind güncel uyumlu sürümleriyle kilitlendi. npm’in önerdiği react-scripts@0.0.0 geçişi uygulanmadı.

| Başlangıç paketi | Önem | Duyuru veya etkilenen alt paket | Yeni kilit |
| --- | --- | --- | --- |
| @jest/core | low | jest-config, jest-runner | Bağımlılık ağacından kaldırıldı |
| @rollup/plugin-node-resolve | low | deepmerge | Bağımlılık ağacından kaldırıldı |
| @svgr/plugin-svgo | high | deepmerge, svgo | Bağımlılık ağacından kaldırıldı |
| @svgr/webpack | low | @svgr/plugin-svgo | Bağımlılık ağacından kaldırıldı |
| @tootallnate/once | low | [GHSA-vpq2-c234-7xj6](https://github.com/advisories/GHSA-vpq2-c234-7xj6) | Bağımlılık ağacından kaldırıldı |
| bfj | high | jsonpath | Bağımlılık ağacından kaldırıldı |
| css-minimizer-webpack-plugin | moderate | serialize-javascript | Bağımlılık ağacından kaldırıldı |
| css-select | high | nth-check | Bağımlılık ağacından kaldırıldı |
| deepmerge | low | [GHSA-gcqx-w48m-w2h4](https://github.com/advisories/GHSA-gcqx-w48m-w2h4) | Bağımlılık ağacından kaldırıldı |
| fork-ts-checker-webpack-plugin | low | deepmerge | Bağımlılık ağacından kaldırıldı |
| glob | moderate | [GHSA-3g3m-2fjr-6pw4](https://github.com/advisories/GHSA-3g3m-2fjr-6pw4), minimatch | Bağımlılık ağacından kaldırıldı |
| http-proxy-agent | low | @tootallnate/once | Bağımlılık ağacından kaldırıldı |
| jest | low | @jest/core, jest-cli | Bağımlılık ağacından kaldırıldı |
| jest-cli | low | @jest/core, jest-config | Bağımlılık ağacından kaldırıldı |
| jest-config | low | deepmerge, jest-environment-jsdom, jest-runner | Bağımlılık ağacından kaldırıldı |
| jest-environment-jsdom | low | jsdom | Bağımlılık ağacından kaldırıldı |
| jest-runner | low | jest-environment-jsdom | Bağımlılık ağacından kaldırıldı |
| jest-watch-typeahead | low | jest | Bağımlılık ağacından kaldırıldı |
| jsdom | low | http-proxy-agent | Kilitli sürüm: 29.1.1 |
| jsonpath | high | underscore | Bağımlılık ağacından kaldırıldı |
| minimatch | moderate | [GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249) | Bağımlılık ağacından kaldırıldı |
| nth-check | high | [GHSA-rp65-9cf3-cjxr](https://github.com/advisories/GHSA-rp65-9cf3-cjxr) | Bağımlılık ağacından kaldırıldı |
| postcss | high | [GHSA-7fh5-64p2-3v2j](https://github.com/advisories/GHSA-7fh5-64p2-3v2j), [GHSA-qx2v-qp2m-jg93](https://github.com/advisories/GHSA-qx2v-qp2m-jg93), [GHSA-6g55-p6wh-862q](https://github.com/advisories/GHSA-6g55-p6wh-862q), [GHSA-fxqj-rqcc-2cmp](https://github.com/advisories/GHSA-fxqj-rqcc-2cmp), [GHSA-r28c-9q8g-f849](https://github.com/advisories/GHSA-r28c-9q8g-f849) | Kilitli sürüm: 8.5.32 |
| react-dev-utils | low | fork-ts-checker-webpack-plugin | Bağımlılık ağacından kaldırıldı |
| react-scripts | moderate | @svgr/webpack, css-minimizer-webpack-plugin, jest, jest-watch-typeahead, react-dev-utils, resolve-url-loader, webpack-dev-server, workbox-webpack-plugin | Bağımlılık ağacından kaldırıldı |
| resolve-url-loader | moderate | postcss | Bağımlılık ağacından kaldırıldı |
| rollup-plugin-terser | high | serialize-javascript | Bağımlılık ağacından kaldırıldı |
| serialize-javascript | high | [GHSA-5c6j-r48x-rmvq](https://github.com/advisories/GHSA-5c6j-r48x-rmvq), [GHSA-qj8w-gfj5-8c6v](https://github.com/advisories/GHSA-qj8w-gfj5-8c6v), [GHSA-m5mm-p8h7-m29v](https://github.com/advisories/GHSA-m5mm-p8h7-m29v) | Bağımlılık ağacından kaldırıldı |
| sockjs | moderate | uuid | Bağımlılık ağacından kaldırıldı |
| sucrase | moderate | glob | Kilitli sürüm: 3.35.1 |
| svgo | high | [GHSA-2p49-hgcm-8545](https://github.com/advisories/GHSA-2p49-hgcm-8545), [GHSA-4vpr-x523-8j87](https://github.com/advisories/GHSA-4vpr-x523-8j87), [GHSA-w27v-7q3p-w38r](https://github.com/advisories/GHSA-w27v-7q3p-w38r), css-select | Bağımlılık ağacından kaldırıldı |
| underscore | high | [GHSA-qpx9-hpmf-5gmw](https://github.com/advisories/GHSA-qpx9-hpmf-5gmw) | Bağımlılık ağacından kaldırıldı |
| uuid | moderate | [GHSA-w5hq-g745-h8pq](https://github.com/advisories/GHSA-w5hq-g745-h8pq) | Bağımlılık ağacından kaldırıldı |
| webpack-dev-middleware | high | [GHSA-g84c-rxfj-3j2c](https://github.com/advisories/GHSA-g84c-rxfj-3j2c) | Bağımlılık ağacından kaldırıldı |
| webpack-dev-server | high | [GHSA-9jgg-88mc-972h](https://github.com/advisories/GHSA-9jgg-88mc-972h), [GHSA-4v9v-hfq4-rm2v](https://github.com/advisories/GHSA-4v9v-hfq4-rm2v), [GHSA-79cf-xcqc-c78w](https://github.com/advisories/GHSA-79cf-xcqc-c78w), [GHSA-mx8g-39q3-5c79](https://github.com/advisories/GHSA-mx8g-39q3-5c79), [GHSA-f5vj-f2hx-8m93](https://github.com/advisories/GHSA-f5vj-f2hx-8m93), [GHSA-m28w-2pqf-7qgj](https://github.com/advisories/GHSA-m28w-2pqf-7qgj), sockjs, webpack-dev-middleware | Bağımlılık ağacından kaldırıldı |
| workbox-build | high | @rollup/plugin-node-resolve, rollup-plugin-terser | Bağımlılık ağacından kaldırıldı |
| workbox-webpack-plugin | low | workbox-build | Bağımlılık ağacından kaldırıldı |

Temiz kurulum sonrası `npm ci --include=dev`, `npm audit --omit=dev` ve tam `npm audit` sıfır bilinen npm bulgusu bildirdi.
