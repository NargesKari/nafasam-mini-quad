const sharp=require('C:/Users/m1382/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root='E:/DronePCB/prototype/preview/';
Promise.all([
 ['Perfboard-Controller, IMU and battery sensing.svg','controller.png'],
 ['Perfboard-Motor channels 1 and 2.svg','motor-drivers.png'],
 ['Perfboard-Battery and electronics power.svg','power.png']
].map(([a,b])=>sharp(root+a,{density:180}).resize({width:1800}).flatten({background:'#fff'}).png().toFile(root+b))).catch(e=>{console.error(e);process.exit(1)});
