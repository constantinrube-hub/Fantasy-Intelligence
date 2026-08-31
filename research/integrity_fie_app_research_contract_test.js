const fs=require('fs'),path=require('path');const root=path.resolve(__dirname,'..');
const svc=fs.readFileSync(path.join(root,'app/core/research-report-service.js'),'utf8');const ui=fs.readFileSync(path.join(root,'app/research-report-ui.js'),'utf8');const bridge=fs.readFileSync(path.join(root,'app/core/research-value-finder-bridge.js'),'utf8');const pub=fs.readFileSync(path.join(root,'research/publish_fie_research_app_contract.py'),'utf8');
if(!svc.includes('fie:league-changing')||!svc.includes('/research_pipeline/')||!svc.includes('FIEResearchReportService'))throw new Error('service league isolation contract missing');
if(/sort\(|positionRank\s*=|overallRank\s*=/.test(svc))throw new Error('research service must not calculate ranks');
if(!ui.includes('Canonical app ranking remains owned by the existing projection/draft services'))throw new Error('UI ownership disclaimer missing');
if(!bridge.includes('tr[data-vf-id]')||!bridge.includes('window.renderValueFinder')||/positionRank\s*=|vorp\s*=|rank_edge\s*=/.test(bridge))throw new Error('Value Finder research bridge must be filter-only');
if(!pub.includes("'readiness'")||!pub.includes("'rankings'")||!pub.includes("'report_summary'"))throw new Error('app core research paths missing');
console.log('PASS app research contract: lazy namespaced context, no parallel rank calculation');
