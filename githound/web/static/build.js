/**
 * GitHound Frontend Build Script
 * Simple build and validation for production deployment
 */

import fs from 'fs';
import { execSync } from 'child_process';

const VERSION = '2.0.0';

function log(message) {
  console.log(`🔨 ${message}`);
}

function updateServiceWorkerCache() {
  log('Updating Service Worker cache version...');
  
  try {
    let swContent = fs.readFileSync('service-worker.js', 'utf8');
    const cacheVersion = `githound-v${VERSION}-${Date.now()}`;
    swContent = swContent.replace(
      /const CACHE_NAME = '[^']+'/,
      `const CACHE_NAME = '${cacheVersion}'`
    );
    fs.writeFileSync('service-worker.js', swContent);
    log('✅ Service Worker updated');
  } catch (error) {
    log(`⚠️ Service Worker update failed: ${error.message}`);
  }
}

function generateBuildInfo() {
  log('Generating build information...');
  
  const buildInfo = {
    version: VERSION,
    buildDate: new Date().toISOString(),
    buildId: Math.random().toString(36).substr(2, 9),
    environment: 'production'
  };
  
  fs.writeFileSync('build-info.json', JSON.stringify(buildInfo, null, 2));
  log('✅ Build info generated');
  return buildInfo;
}

function validateBuild() {
  log('Validating build...');
  
  const requiredFiles = [
    'main.js',
    'index.html',
    'service-worker.js',
    'components/core/app.js'
  ];
  
  const missing = requiredFiles.filter(file => !fs.existsSync(file));
  
  if (missing.length > 0) {
    log(`❌ Missing files: ${missing.join(', ')}`);
    return false;
  }
  
  log('✅ Build validation passed');
  return true;
}

function main() {
  console.log('🚀 GitHound Frontend Build\n');
  
  if (!validateBuild()) {
    process.exit(1);
  }
  
  const buildInfo = generateBuildInfo();
  updateServiceWorkerCache();
  
  console.log('\n🎉 Build completed successfully!');
  console.log(`📦 Version: ${buildInfo.version}`);
  console.log(`🆔 Build ID: ${buildInfo.buildId}`);
  console.log('🚀 Ready for deployment!');
}

main();
