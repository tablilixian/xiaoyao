// ==================== 全局变量 ====================
let simulation, svg, g, zoom;
let nodes = [], links = [];
let animationRunning = true;

// ==================== 初始化 ====================
function init() {
    loadData().then(data => {
        buildGraphData(data);
        renderGraph();
        initRelationChart();
        initCharacterList();
        initFilters();
        initSearch();
        document.getElementById('loading').style.display = 'none';
    });
}

// ==================== Tab 切换 ====================
document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', function() {
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        this.classList.add('active');
        const tabName = this.dataset.tab;
        document.querySelectorAll('.main-panel').forEach(p => p.style.display = 'none');
        
        if (tabName === 'graph') {
            document.getElementById('graph-panel').style.display = '';
        } else if (tabName === 'faction') {
            document.getElementById('faction-panel').style.display = '';
            if (!factionInitialized) { initFactionGraph(); factionInitialized = true; }
        } else if (tabName === 'worldmap') {
            document.getElementById('worldmap-panel').style.display = '';
            if (!locationInitialized) { initLocationGraph(); locationInitialized = true; }
        } else if (tabName === 'timeline') {
            document.getElementById('timeline-panel').style.display = '';
            if (!timelineInitialized) { initTimeline(); timelineInitialized = true; }
        } else if (tabName === 'stats') {
            document.getElementById('stats-panel').style.display = '';
        }
    });
});

// ==================== 关系图谱 ====================
async function loadData() {
    try {
        const response = await fetch('../novel_data/knowledge/knowledge_core.json');
        if (response.ok) return await response.json();
    } catch (e) {
        console.error('Failed to load data:', e);
    }
    return generateMockData();
}

function generateMockData() {
    const characters = ['崔小玄', '武翩跹', '婀妍', '程水若', '方少麟', '飞萝', '崔采婷', '碧怜怜', '逍遥郎君', '皇后'];
    const relations = ['盟友', '敌对', '师徒', '情感'];
    const data = { nodes: [], links: [] };
    characters.forEach((name, i) => {
        data.nodes.push({ id: name, name, gender: i % 2 === 0 ? '男' : '女', count: 100 - i * 10 });
    });
    for (let i = 0; i < 20; i++) {
        const source = Math.floor(Math.random() * characters.length);
        let target = Math.floor(Math.random() * characters.length);
        if (source !== target) {
            data.links.push({ source: characters[source], target: characters[target], type: relations[Math.floor(Math.random() * relations.length)] });
        }
    }
    return data;
}

function buildGraphData(data) {
    const relationships = data.relationships || [];
    const nodeMap = new Map();
    links = [];
    
    const typeMap = {
        'master': '师徒',
        'superior': '师徒',
        'senior': '盟友',
        'friend': '盟友',
        'enemy': '敌对',
        'rival': '敌对',
        'lover': '情感',
        'family': '情感',
        ' disciple': '师徒'
    };
    
    relationships.forEach(rel => {
        const type = typeMap[rel.type] || '盟友';
        
        if (!nodeMap.has(rel.source)) {
            nodeMap.set(rel.source, { id: rel.source, name: rel.source, gender: '男', count: 0 });
        }
        if (!nodeMap.has(rel.target)) {
            nodeMap.set(rel.target, { id: rel.target, name: rel.target, gender: '女', count: 0 });
        }
        
        nodeMap.get(rel.source).count++;
        nodeMap.get(rel.target).count++;
        
        links.push({ source: rel.source, target: rel.target, type: type });
    });
    
    nodes = Array.from(nodeMap.values());
}

function renderGraph() {
    const container = document.getElementById('graph-svg');
    const width = container.clientWidth;
    const height = container.clientHeight;
    container.innerHTML = '';

    svg = d3.select('#graph-svg').append('svg').attr('width', width).attr('height', height);
    zoom = d3.zoom().scaleExtent([0.1, 4]).on('zoom', e => g.attr('transform', e.transform));
    svg.call(zoom);
    g = svg.append('g');

    simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(25));

    const link = g.append('g').selectAll('line').data(links).join('line')
        .attr('stroke', d => getRelationColor(d.type)).attr('stroke-width', 2).attr('stroke-opacity', 0.6);

    const node = g.append('g').selectAll('g').data(nodes).join('g')
        .call(d3.drag().on('start', dragStarted).on('drag', dragged).on('end', dragEnded));

    node.append('circle').attr('r', 15).attr('fill', d => d.gender === '女' ? '#c75b5b' : '#5a9a8f')
        .attr('stroke', '#e8e4dc').attr('stroke-width', 2).style('cursor', 'pointer');
    node.append('text').text(d => d.name.substring(0, 2)).attr('text-anchor', 'middle').attr('dy', 4)
        .attr('font-size', 10).attr('fill', '#fff').attr('font-weight', 600).style('pointer-events', 'none');

    node.on('mouseover', showTooltip).on('mouseout', hideTooltip).on('click', focusNode);
    simulation.on('tick', () => {
        link.attr('x1', d => d.source.x).attr('y1', d => d.source.y).attr('x2', d => d.target.x).attr('y2', d => d.target.y);
        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
}

function getRelationColor(type) {
    const colors = { 
        '盟友': '#5a9a8f', 
        '敌对': '#c75b5b', 
        '师徒': '#d4a574', 
        '情感': '#6b8cae',
        'master': '#d4a574',
        'superior': '#d4a574',
        'senior': '#5a9a8f',
        'friend': '#5a9a8f',
        'enemy': '#c75b5b',
        'rival': '#c75b5b',
        'lover': '#6b8cae',
        'family': '#6b8cae'
    };
    return colors[type] || '#888';
}

function dragStarted(e, d) { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }
function dragged(e, d) { d.fx = e.x; d.fy = e.y; }
function dragEnded(e, d) { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }

function showTooltip(e, d) {
    const tooltip = document.getElementById('tooltip');
    document.getElementById('tooltip-title').textContent = d.name;
    document.getElementById('tooltip-content').innerHTML = `性别: ${d.gender || '未知'}<br>出场次数: ${d.count || 0}`;
    tooltip.style.left = (e.pageX + 15) + 'px';
    tooltip.style.top = (e.pageY + 15) + 'px';
    tooltip.classList.add('visible');
}

function hideTooltip() { document.getElementById('tooltip').classList.remove('visible'); }

function focusNode(e, d) {
    g.selectAll('line').attr('stroke-opacity', l => (l.source.id === d.id || l.target.id === d.id) ? 1 : 0.05);
    g.selectAll('g').attr('opacity', n => (n.id === d.id || links.some(l => (l.source.id === d.id && l.target.id === n.id) || (l.target.id === d.id && l.source.id === n.id))) ? 1 : 0.1);
}

function resetHighlight() { g.selectAll('line').attr('stroke-opacity', 0.6); g.selectAll('g').attr('opacity', 1); }

function resetZoom() { svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity); }
function toggleAnimation() { animationRunning = !animationRunning; animationRunning ? simulation.restart() : simulation.stop(); }

function initRelationChart() {
    const chart = echarts.init(document.getElementById('relation-chart'));
    const typeCount = {};
    links.forEach(l => { typeCount[l.type] = (typeCount[l.type] || 0) + 1; });
    const data = Object.entries(typeCount).map(([name, value]) => ({ name, value }));
    chart.setOption({
        backgroundColor: 'transparent',
        tooltip: { trigger: 'item', backgroundColor: 'rgba(26,26,37,0.95)', borderColor: '#2a2a3a', textStyle: { color: '#e8e4dc' } },
        series: [{ type: 'pie', radius: ['35%', '65%'], data, label: { color: '#a09888', fontSize: 10 }, itemStyle: { borderRadius: 5, borderColor: '#1a1a25', borderWidth: 2 },
            color: ['#5a9a8f', '#c75b5b', '#d4a574', '#6b8cae'] }]
    });
    window.addEventListener('resize', () => chart.resize());
}

function initCharacterList() {
    const list = document.getElementById('character-list');
    const sorted = [...nodes].sort((a, b) => (b.count || 0) - (a.count || 0));
    list.innerHTML = sorted.slice(0, 10).map(c => `
        <div class="character-item" onclick="focusCharacter('${c.name}')">
            <div class="character-avatar" style="background:${c.gender === '女' ? '#c75b5b' : '#5a9a8f'}">${c.name.substring(0, 1)}</div>
            <div class="character-info"><div class="character-name">${c.name}</div><div class="character-meta">${c.gender || '未知'}</div></div>
            <div class="character-count">${c.count || 0}</div>
        </div>
    `).join('');
}

function focusCharacter(name) {
    const node = nodes.find(n => n.name === name);
    if (node) focusNode(null, node);
}

function initFilters() {
    document.getElementById('relation-filters').querySelectorAll('.filter-tag').forEach(tag => {
        tag.addEventListener('click', function() {
            document.getElementById('relation-filters').querySelectorAll('.filter-tag').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            const type = this.dataset.type;
            if (type === 'all') { resetHighlight(); return; }
            g.selectAll('line').attr('stroke-opacity', l => l.type === type ? 0.8 : 0.05);
            g.selectAll('g').attr('opacity', d => links.some(l => (l.source.id === d.id || l.target.id === d.id) && l.type === type) ? 1 : 0.1);
        });
    });
}

function initSearch() {
    document.getElementById('search-input').addEventListener('input', function() {
        const query = this.value.toLowerCase();
        if (!query) { resetHighlight(); return; }
        const matched = nodes.filter(n => n.name.toLowerCase().includes(query));
        g.selectAll('g').attr('opacity', d => matched.some(m => m.id === d.id) ? 1 : 0.1);
        g.selectAll('line').attr('stroke-opacity', 0.05);
    });
}

// ==================== 势力关系图 ====================
let factionSimulation, factionSvg, factionG, factionZoom;
let factionNodes = [], factionLinks = [];
let factionInitialized = false;
let factionsData = {};
let allCharactersData = [];
let factionToCharacters = {};

const factionTypeColors = {
    '门派': '#d4a574', '魔族': '#c75b5b', '朝廷': '#6b8cae', '军队': '#5a7a9a',
    '政治派系': '#9b8aa5', '民间势力': '#8b9a6b', '天界势力': '#e8d44d', '妖族': '#5a9a8f'
};

function getFactionColor(type) { return factionTypeColors[type] || '#5c5c6e'; }

async function loadFactionsData() {
    try {
        const response = await fetch('../novel_data/index/factions.json');
        if (response.ok) { factionsData = await response.json(); console.log(`Loaded ${Object.keys(factionsData).length} factions`); }
    } catch (e) { console.error('Failed to load factions:', e); }
}

async function loadCharactersForFactions() {
    for (const vol of [1, 2, 3]) {
        try {
            const response = await fetch(`../novel_data/volumes/volume_${vol}.json`);
            if (response.ok) { const data = await response.json(); if (data.characters) allCharactersData.push(...data.characters); }
        } catch (e) {}
    }
    buildFactionToCharactersMap();
}

function buildFactionToCharactersMap() {
    for (const char of allCharactersData) {
        if (!char.faction) continue;
        let mainFaction = char.faction.split('·')[0].split('（')[0].trim();
        if (!factionToCharacters[mainFaction]) factionToCharacters[mainFaction] = [];
        if (!factionToCharacters[mainFaction].some(c => c.name === char.name)) {
            factionToCharacters[mainFaction].push({ name: char.name, gender: char.gender || '未知', identity: char.identity || '' });
        }
    }
}

function buildFactionGraphData() {
    const nodeMap = new Map();
    for (const [name, data] of Object.entries(factionsData)) {
        const importance = typeof data.importance === 'number' ? data.importance : 3;
        nodeMap.set(name, { id: name, name, type: data.type || '未知', leader: data.leader || '未知', importance, allies: data.allies || [], enemies: data.enemies || [], radius: 8 + importance * 4 });
    }
    for (const [name, data] of Object.entries(factionsData)) {
        if (data.allies) data.allies.forEach(ally => { const clean = ally.replace(/（.*?）/g, '').trim(); if (nodeMap.has(clean)) factionLinks.push({ source: name, target: clean, type: 'ally' }); });
        if (data.enemies) data.enemies.forEach(enemy => { const clean = enemy.replace(/（.*?）/g, '').trim(); if (nodeMap.has(clean)) factionLinks.push({ source: name, target: clean, type: 'enemy' }); });
    }
    factionNodes = Array.from(nodeMap.values());
}

function initFactionGraph() {
    Promise.all([loadFactionsData(), loadCharactersForFactions()]).then(() => {
        buildFactionGraphData();
        renderFactionGraph();
        initFactionTypeChart();
        initFactionList();
        initFactionTypeFilters();
        initFactionSearch();
        document.getElementById('faction-loading').style.display = 'none';
    });
}

function renderFactionGraph() {
    const container = document.getElementById('faction-graph-svg');
    const width = container.clientWidth;
    const height = container.clientHeight;
    container.innerHTML = '';

    factionSvg = d3.select('#faction-graph-svg').append('svg').attr('width', width).attr('height', height);
    factionZoom = d3.zoom().scaleExtent([0.1, 4]).on('zoom', e => factionG.attr('transform', e.transform));
    factionSvg.call(factionZoom);
    factionG = factionSvg.append('g');

    factionSimulation = d3.forceSimulation(factionNodes)
        .force('link', d3.forceLink(factionLinks).id(d => d.id).distance(d => d.type === 'enemy' ? 150 : 100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => d.radius + 5));

    const link = factionG.append('g').selectAll('line').data(factionLinks).join('line')
        .attr('stroke', d => d.type === 'ally' ? '#5a9a8f' : '#c75b5b').attr('stroke-width', 2).attr('stroke-opacity', 0.5)
        .attr('stroke-dasharray', d => d.type === 'enemy' ? '5,3' : 'none');

    const node = factionG.append('g').selectAll('g').data(factionNodes).join('g')
        .call(d3.drag().on('start', e => { if (!e.active) factionSimulation.alphaTarget(0.3).restart(); e.subject.fx = e.subject.x; e.subject.fy = e.subject.y; })
            .on('drag', e => { e.subject.fx = e.x; e.subject.fy = e.y; })
            .on('end', e => { if (!e.active) factionSimulation.alphaTarget(0); e.subject.fx = null; e.subject.fy = null; }));

    node.append('circle').attr('r', d => d.radius).attr('fill', d => getFactionColor(d.type)).attr('fill-opacity', 0.7)
        .attr('stroke', d => getFactionColor(d.type)).attr('stroke-width', d => d.importance >= 4 ? 3 : 1.5).style('cursor', 'pointer');

    node.append('text').text(d => d.name).attr('x', d => d.radius + 5).attr('y', 4)
        .attr('font-size', d => d.importance >= 4 ? 12 : 10).attr('fill', '#e8e4dc').style('pointer-events', 'none');

    node.on('mouseover', showFactionTooltip).on('mouseout', hideTooltip).on('click', (e, d) => { focusOnFactionNode(d); showFactionMembers(d.name); });
    factionSimulation.on('tick', () => {
        link.attr('x1', d => d.source.x).attr('y1', d => d.source.y).attr('x2', d => d.target.x).attr('y2', d => d.target.y);
        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
}

function showFactionTooltip(e, d) {
    const tooltip = document.getElementById('tooltip');
    document.getElementById('tooltip-title').textContent = d.name;
    document.getElementById('tooltip-content').innerHTML = `类型: ${d.type}<br>首领: ${d.leader}<br>重要度: ${'★'.repeat(d.importance)}`;
    tooltip.style.left = (e.pageX + 15) + 'px';
    tooltip.style.top = (e.pageY + 15) + 'px';
    tooltip.classList.add('visible');
}

function focusOnFactionNode(d) {
    const scale = 2;
    const x = -d.x * scale + factionSvg.attr('width') / 2;
    const y = -d.y * scale + factionSvg.attr('height') / 2;
    factionSvg.transition().duration(750).call(factionZoom.transform, d3.zoomIdentity.translate(x, y).scale(scale));
}

function showFactionMembers(factionName) {
    const panel = document.getElementById('faction-members-panel');
    const title = document.getElementById('faction-members-title');
    const list = document.getElementById('faction-members-list');
    let members = factionToCharacters[factionName] || [];
    if (members.length === 0) { title.textContent = `${factionName} - 成员`; list.innerHTML = '<div style="padding: 20px; color: #888; text-align: center;">暂无成员数据</div>'; panel.style.display = 'block'; return; }
    title.textContent = `${factionName} - ${members.length}位成员`;
    list.innerHTML = members.map(c => `<div class="character-item"><div class="character-avatar" style="background:${c.gender === '女' ? '#c75b5b' : '#5a9a8f'}">${c.name.substring(0, 1)}</div><div class="character-info"><div class="character-name">${c.name}</div><div class="character-meta">${c.gender}</div></div></div>`).join('');
    panel.style.display = 'block';
}

function initFactionTypeChart() {
    const chart = echarts.init(document.getElementById('faction-type-chart'));
    const typeCount = {};
    factionNodes.forEach(n => { typeCount[n.type] = (typeCount[n.type] || 0) + 1; });
    const data = Object.entries(typeCount).map(([name, value]) => ({ name, value }));
    chart.setOption({ backgroundColor: 'transparent', tooltip: { trigger: 'item', backgroundColor: 'rgba(26,26,37,0.95)', textStyle: { color: '#e8e4dc' } },
        series: [{ type: 'pie', radius: ['35%', '65%'], data, label: { color: '#a09888', fontSize: 10 }, itemStyle: { borderRadius: 5 } }] });
}

function initFactionList() {
    const list = document.getElementById('faction-list');
    const sorted = [...factionNodes].sort((a, b) => b.importance - a.importance);
    list.innerHTML = sorted.map(f => `<div class="character-item" onclick="focusFaction('${f.name}')"><div class="character-avatar" style="background:${getFactionColor(f.type)}">${f.name.substring(0, 2)}</div><div class="character-info"><div class="character-name">${f.name}</div><div class="character-meta">${f.type}</div></div><div class="character-count">${'★'.repeat(f.importance)}</div></div>`).join('');
}

function focusFaction(name) { const node = factionNodes.find(n => n.name === name); if (node) focusOnFactionNode(node); }

function initFactionTypeFilters() {
    const container = document.getElementById('faction-type-filters');
    const types = new Set(factionNodes.map(n => n.type));
    container.innerHTML = '<span class="filter-tag active" data-type="all">全部</span>';
    types.forEach(t => { container.innerHTML += `<span class="filter-tag" data-type="${t}">${t}</span>`; });
    container.querySelectorAll('.filter-tag').forEach(tag => {
        tag.addEventListener('click', function() {
            container.querySelectorAll('.filter-tag').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            const type = this.dataset.type;
            if (type === 'all') { factionG.selectAll('g').attr('opacity', 1); factionG.selectAll('line').attr('stroke-opacity', 0.5); }
            else { factionG.selectAll('g').attr('opacity', d => d.type === type ? 1 : 0.1); factionG.selectAll('line').attr('stroke-opacity', 0.05); }
        });
    });
}

function initFactionSearch() {
    document.getElementById('faction-search').addEventListener('input', function() {
        const query = this.value.toLowerCase();
        if (!query) { factionG.selectAll('g').attr('opacity', 1); factionG.selectAll('line').attr('stroke-opacity', 0.5); return; }
        const matched = factionNodes.filter(n => n.name.toLowerCase().includes(query));
        factionG.selectAll('g').attr('opacity', d => matched.some(m => m.id === d.id) ? 1 : 0.1);
        factionG.selectAll('line').attr('stroke-opacity', 0.05);
    });
}

function resetFactionZoom() { factionSvg.transition().duration(750).call(factionZoom.transform, d3.zoomIdentity); }
function toggleFactionAnimation() { factionSimulation.stop(); }

// ==================== 世界地点图 ====================
let locationSimulation, locationSvg, locationG, locationZoom;
let locationNodes = [], locationLinks = [];
let locationInitialized = false;
let locationsData = {};

function getLocationColor(type) {
    if (!type) return '#5c5c6e';
    const t = type.toLowerCase();
    if (/山|岭|峰|谷|原|林|海|湖|河|泽|岛|崖|峡/.test(t)) return '#5a9a8f';
    if (/城|镇|州|县|村|庄|坊/.test(t)) return '#6b8cae';
    if (/宫|殿|阁|楼|轩|亭|榭|苑|园|堂|观|寺|庙|府|邸/.test(t)) return '#d4a574';
    if (/秘|魔|邪|幻|虚|异|禁/.test(t)) return '#9a6ad4';
    return '#5c5c6e';
}

async function loadLocationsData() {
    try {
        const [mainResp, minorResp] = await Promise.all([fetch('../novel_data/index/locations.json'), fetch('../novel_data/index/locations_minor.json')]);
        if (mainResp.ok) Object.assign(locationsData, await mainResp.json());
        if (minorResp.ok) Object.assign(locationsData, await minorResp.json());
        console.log(`Loaded ${Object.keys(locationsData).length} locations`);
    } catch (e) { console.error('Failed to load locations:', e); }
}

function buildLocationGraphData() {
    const nodeMap = new Map();
    for (const [name, data] of Object.entries(locationsData)) {
        nodeMap.set(name, { id: name, name, type: data.type || '未知', importance: data.importance || 2, parent: data.parent || null, volumes: data.volumes || [], radius: 4 + (data.importance || 2) * 3 });
    }
    for (const [name, data] of Object.entries(locationsData)) {
        if (!data.parent) continue;
        let matchedParent = null;
        if (nodeMap.has(data.parent)) matchedParent = data.parent;
        else for (const key of nodeMap.keys()) { if (data.parent.includes(key) || key.includes(data.parent)) { matchedParent = key; break; } }
        if (matchedParent && matchedParent !== name) locationLinks.push({ source: matchedParent, target: name });
    }
    locationNodes = Array.from(nodeMap.values());
}

function initLocationGraph() {
    loadLocationsData().then(() => {
        buildLocationGraphData();
        renderLocationGraph();
        initLocationTypeChart();
        initLocationImportanceFilters();
        initLocationSearch();
        document.getElementById('location-loading').style.display = 'none';
    });
}

function renderLocationGraph() {
    const container = document.getElementById('location-graph-svg');
    const width = container.clientWidth;
    const height = container.clientHeight;
    container.innerHTML = '';

    locationSvg = d3.select('#location-graph-svg').append('svg').attr('width', width).attr('height', height);
    locationZoom = d3.zoom().scaleExtent([0.05, 5]).on('zoom', e => locationG.attr('transform', e.transform));
    locationSvg.call(locationZoom);
    locationG = locationSvg.append('g');

    locationSimulation = d3.forceSimulation(locationNodes)
        .force('link', d3.forceLink(locationLinks).id(d => d.id).distance(50).strength(0.3))
        .force('charge', d3.forceManyBody().strength(-60))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => d.radius + 3));

    const link = locationG.append('g').selectAll('line').data(locationLinks).join('line').attr('stroke', '#3a3a5a').attr('stroke-width', 1).attr('stroke-opacity', 0.5);

    const node = locationG.append('g').selectAll('g').data(locationNodes).join('g')
        .call(d3.drag().on('start', e => { if (!e.active) locationSimulation.alphaTarget(0.3).restart(); e.subject.fx = e.subject.x; e.subject.fy = e.subject.y; })
            .on('drag', e => { e.subject.fx = e.x; e.subject.fy = e.y; })
            .on('end', e => { if (!e.active) locationSimulation.alphaTarget(0); e.subject.fx = null; e.subject.fy = null; }));

    node.append('circle').attr('r', d => d.radius).attr('fill', d => getLocationColor(d.type)).attr('fill-opacity', 0.7)
        .attr('stroke', d => getLocationColor(d.type)).attr('stroke-width', d => d.importance >= 4 ? 2 : 1).style('cursor', 'pointer');

    node.filter(d => d.importance >= 3).append('text').text(d => d.name.length > 5 ? d.name.substring(0, 5) + '…' : d.name)
        .attr('x', d => d.radius + 4).attr('y', 4).attr('font-size', 9).attr('fill', '#e8e4dc').style('pointer-events', 'none');

    node.on('mouseover', showLocationTooltip).on('mouseout', hideTooltip).on('click', (e, d) => { showLocationDetail(d); focusOnLocationNode(d); });
    locationSimulation.on('tick', () => {
        link.attr('x1', d => d.source.x).attr('y1', d => d.source.y).attr('x2', d => d.target.x).attr('y2', d => d.target.y);
        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
}

function showLocationTooltip(e, d) {
    const tooltip = document.getElementById('tooltip');
    document.getElementById('tooltip-title').textContent = d.name;
    document.getElementById('tooltip-content').innerHTML = `类型: ${d.type}<br>重要度: ${'★'.repeat(d.importance)}`;
    tooltip.style.left = (e.pageX + 15) + 'px';
    tooltip.style.top = (e.pageY + 15) + 'px';
    tooltip.classList.add('visible');
}

function showLocationDetail(d) {
    const detail = document.getElementById('location-detail');
    const children = locationLinks.filter(l => l.source.id === d.id).map(l => l.target.name);
    detail.innerHTML = `<div style="font-size: 16px; font-weight: 700; color: #e8e4dc; margin-bottom: 10px;">${d.name}</div>
        <div style="font-size: 12px; color: #888;">类型: <span style="color: ${getLocationColor(d.type)};">${d.type}</span></div>
        <div style="font-size: 12px; color: #888;">重要度: <span style="color: #d4a574;">${'★'.repeat(d.importance)}</span></div>
        ${d.parent ? `<div style="font-size: 12px; color: #888;">所属: ${d.parent}</div>` : ''}
        ${children.length > 0 ? `<div style="margin-top: 10px; font-size: 12px; color: #888;">子地点: ${children.slice(0, 5).join('、')}${children.length > 5 ? '...' : ''}</div>` : ''}`;
}

function focusOnLocationNode(d) {
    const scale = 2.5;
    const x = -d.x * scale + locationSvg.attr('width') / 2;
    const y = -d.y * scale + locationSvg.attr('height') / 2;
    locationSvg.transition().duration(750).call(locationZoom.transform, d3.zoomIdentity.translate(x, y).scale(scale));
}

function initLocationTypeChart() {
    const chart = echarts.init(document.getElementById('location-type-chart'));
    const typeCount = {};
    locationNodes.forEach(n => { typeCount[n.type] = (typeCount[n.type] || 0) + 1; });
    const data = Object.entries(typeCount).slice(0, 8).map(([name, value]) => ({ name, value }));
    chart.setOption({ backgroundColor: 'transparent', tooltip: { trigger: 'item' }, series: [{ type: 'pie', radius: ['35%', '65%'], data, label: { color: '#a09888', fontSize: 9 } }] });
}

function initLocationImportanceFilters() {
    document.getElementById('location-importance-filters').querySelectorAll('.filter-tag').forEach(tag => {
        tag.addEventListener('click', function() {
            document.getElementById('location-importance-filters').querySelectorAll('.filter-tag').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            const imp = this.dataset.imp;
            if (imp === 'all') { locationG.selectAll('g').attr('opacity', 1); locationG.selectAll('line').attr('stroke-opacity', 0.5); }
            else { const minImp = parseInt(imp); locationG.selectAll('g').attr('opacity', d => d.importance >= minImp ? 1 : 0.08); locationG.selectAll('line').attr('stroke-opacity', 0.05); }
        });
    });
}

function initLocationSearch() {
    document.getElementById('location-search').addEventListener('input', function() {
        const query = this.value.toLowerCase();
        if (!query) { locationG.selectAll('g').attr('opacity', 1); locationG.selectAll('line').attr('stroke-opacity', 0.5); return; }
        const matched = locationNodes.filter(n => n.name.toLowerCase().includes(query));
        locationG.selectAll('g').attr('opacity', d => matched.some(m => m.id === d.id) ? 1 : 0.08);
        locationG.selectAll('line').attr('stroke-opacity', 0.05);
    });
}

function resetLocationZoom() { locationSvg.transition().duration(750).call(locationZoom.transform, d3.zoomIdentity); }
function toggleLocationAnimation() { locationSimulation.stop(); }

// 启动
init();
