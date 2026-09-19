const sharp = require('C:/Users/m1382/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
Promise.all(['board-final','battery-plane'].map(n => sharp(`E:/DronePCB/preview/${n}.svg`, {density:600}).resize({width:1600}).flatten({background:'#ffffff'}).png().toFile(`E:/DronePCB/preview/${n}.png`))).catch(e=>{console.error(e);process.exit(1)});
