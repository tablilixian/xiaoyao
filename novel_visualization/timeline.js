// ==================== 故事时间线 ====================
let timelineData = {};
let currentVolume = '1';
let timelineInitialized = false;
let selectedChapter = null;

async function loadTimelineData(volume) {
    try {
        const response = await fetch(`../novel_data/volumes/volume_${volume}.json`);
        if (response.ok) {
            const data = await response.json();
            timelineData[volume] = data;
            console.log(`Loaded volume ${volume}: ${data.meta?.timeline_count || 0} timeline entries, ${data.events?.length || 0} events`);
            return data;
        }
    } catch (e) {
        console.error(`Failed to load volume ${volume}:`, e);
    }
    return null;
}

async function initTimeline() {
    await loadTimelineData('1');
    renderTimeline('1');
    updateVolumeStats('1');
    initTimelineFilters();
    initTimelineVolumeSelect();
    document.getElementById('timeline-loading').style.display = 'none';
}

function renderTimeline(volume) {
    const data = timelineData[volume];
    if (!data) return;

    const wrapper = document.getElementById('timeline-wrapper');
    wrapper.innerHTML = '';

    const chapterEvents = {};
    
    if (data.timeline) {
        data.timeline.forEach(item => {
            const chapter = item.chapter || '未知';
            if (!chapterEvents[chapter]) {
                chapterEvents[chapter] = {
                    chapter: chapter,
                    time: item.time || '',
                    events: [],
                    characters: new Set(),
                    locations: new Set()
                };
            }
            chapterEvents[chapter].events.push({
                type: 'background',
                desc: item.event,
                characters: item.characters || [],
                location: item.location
            });
            if (item.characters) {
                item.characters.forEach(c => chapterEvents[chapter].characters.add(c));
            }
            if (item.location) {
                chapterEvents[chapter].locations.add(item.location);
            }
        });
    }

    if (data.events) {
        data.events.forEach(evt => {
            const chapter = evt.chapter || '未知';
            if (!chapterEvents[chapter]) {
                chapterEvents[chapter] = {
                    chapter: chapter,
                    events: [],
                    characters: new Set(),
                    locations: new Set()
                };
            }
            chapterEvents[chapter].events.push({
                type: evt.type || '日常',
                desc: evt.summary,
                outcome: evt.outcome,
                participants: evt.participants || [],
                location: evt.location,
                intimacy: evt.intimacy_changes
            });
            if (evt.participants) {
                evt.participants.forEach(p => chapterEvents[chapter].characters.add(p));
            }
            if (evt.location) {
                chapterEvents[chapter].locations.add(evt.location);
            }
        });
    }

    const sortedChapters = Object.keys(chapterEvents).sort((a, b) => {
        if (a === '楔子') return -1;
        if (b === '楔子') return 1;
        const numA = parseInt(a.replace(/[^\d]/g, '')) || 0;
        const numB = parseInt(b.replace(/[^\d]/g, '')) || 0;
        return numA - numB;
    });

    sortedChapters.forEach((chapter, index) => {
        const chapterData = chapterEvents[chapter];
        const div = document.createElement('div');
        div.className = 'timeline-chapter';
        div.dataset.chapter = chapter;
        div.dataset.index = index;

        const typeCount = {};
        chapterData.events.forEach(e => {
            const t = e.type || '日常';
            typeCount[t] = (typeCount[t] || 0) + 1;
        });

        let eventTagsHtml = '';
        if (typeCount['战斗']) eventTagsHtml += `<span class="timeline-event-tag battle">⚔️ ${typeCount['战斗']}</span>`;
        if (typeCount['阴谋']) eventTagsHtml += `<span class="timeline-event-tag conspiracy">📜 ${typeCount['阴谋']}</span>`;
        if (typeCount['日常']) eventTagsHtml += `<span class="timeline-event-tag daily">🏠 ${typeCount['日常']}</span>`;
        if (typeCount['情感']) eventTagsHtml += `<span class="timeline-event-tag emotion">💕 ${typeCount['情感']}</span>`;

        const characters = Array.from(chapterData.characters).slice(0, 5);
        let charsHtml = '<div class="timeline-characters">';
        characters.forEach(char => {
            const initial = char.substring(0, 1);
            charsHtml += `<div class="timeline-char-avatar" title="${char}">${initial}</div>`;
        });
        if (chapterData.characters.size > 5) {
            charsHtml += `<div style="font-size: 11px; color: #888; margin-left: 5px;">+${chapterData.characters.size - 5}</div>`;
        }
        charsHtml += '</div>';

        let desc = '';
        if (chapterData.events.length > 0) {
            const firstEvent = chapterData.events[0];
            desc = firstEvent.desc ? firstEvent.desc.substring(0, 60) + (firstEvent.desc.length > 60 ? '...' : '') : '';
        }

        div.innerHTML = `
            <div class="timeline-chapter-title">${chapter}</div>
            <div class="timeline-chapter-desc">${desc || chapterData.time || ''}</div>
            <div class="timeline-events">${eventTagsHtml}</div>
            ${charsHtml}
        `;

        div.addEventListener('click', () => selectChapter(chapter, chapterData, volume));
        wrapper.appendChild(div);
    });
}

function selectChapter(chapter, chapterData, volume) {
    document.querySelectorAll('.timeline-chapter').forEach(el => el.classList.remove('active'));
    document.querySelector(`.timeline-chapter[data-chapter="${chapter}"]`)?.classList.add('active');
    selectedChapter = chapter;

    const detail = document.getElementById('chapter-detail');
    
    const typeCount = {};
    let hasDeath = false, hasUpgrade = false, hasItem = false;
    
    chapterData.events.forEach(e => {
        const t = e.type || '日常';
        typeCount[t] = (typeCount[t] || 0) + 1;
        if (e.desc && /死|亡|杀|陨/.test(e.desc)) hasDeath = true;
        if (e.desc && /突破|升级|进阶|领悟/.test(e.desc)) hasUpgrade = true;
        if (e.desc && /获得|得到|拾取|赐予/.test(e.desc)) hasItem = true;
    });

    let html = `
        <div style="margin-bottom: 15px;">
            <div style="font-size: 18px; font-weight: 700; color: #e8e4dc; margin-bottom: 5px;">${chapter}</div>
            ${chapterData.time ? `<div style="font-size: 12px; color: #888;">📅 ${chapterData.time}</div>` : ''}
        </div>
    `;

    const locations = Array.from(chapterData.locations);
    if (locations.length > 0) {
        html += `<div style="margin-bottom: 12px;"><span style="color: #888; font-size: 12px;">📍 地点：</span><span style="color: #d4a574;">${locations.join('、')}</span></div>`;
    }

    const allCharacters = Array.from(chapterData.characters);
    if (allCharacters.length > 0) {
        html += `<div style="margin-bottom: 12px;"><span style="color: #888; font-size: 12px;">👥 出场角色：</span><div style="display: flex; flex-wrap: wrap; gap: 5px; margin-top: 5px;">`;
        allCharacters.forEach(char => {
            html += `<span style="padding: 2px 8px; background: rgba(212,165,116,0.15); border-radius: 10px; font-size: 12px; color: #d4a574;">${char}</span>`;
        });
        html += '</div></div>';
    }

    // 特殊事件标记
    let specialEvents = [];
    if (hasDeath) specialEvents.push('<span style="color: #c75b5b;">💀 有角色死亡</span>');
    if (hasUpgrade) specialEvents.push('<span style="color: #6b8cae;">⬆️ 有角色突破</span>');
    if (hasItem) specialEvents.push('<span style="color: #d4a574;">🏆 有宝物获得</span>');
    if (specialEvents.length > 0) {
        html += `<div style="margin-bottom: 12px; padding: 8px; background: rgba(255,255,255,0.03); border-radius: 8px;">${specialEvents.join(' ')}</div>`;
    }

    // 事件列表
    if (chapterData.events.length > 0) {
        html += `<div style="margin-top: 15px;"><div style="font-size: 13px; color: #888; margin-bottom: 8px;">📋 事件列表</div>`;
        chapterData.events.slice(0, 5).forEach((evt, idx) => {
            const typeIcon = evt.type === '战斗' ? '⚔️' : evt.type === '阴谋' ? '📜' : evt.type === '情感' ? '💕' : '🏠';
            const typeClass = evt.type === '战斗' ? 'battle' : evt.type === '阴谋' ? 'conspiracy' : evt.type === '情感' ? 'emotion' : 'daily';
            html += `
                <div style="padding: 8px; margin-bottom: 6px; background: rgba(255,255,255,0.03); border-radius: 6px; border-left: 3px solid ${typeClass === 'battle' ? '#c75b5b' : typeClass === 'conspiracy' ? '#9a6ad4' : typeClass === 'emotion' ? '#5a9a8f' : '#d4a574'};">
                    <div style="font-size: 11px; color: #888; margin-bottom: 2px;">${typeIcon} ${evt.type || '日常'}</div>
                    <div style="font-size: 12px; color: #e8e4dc; line-height: 1.4;">${evt.desc ? evt.desc.substring(0, 80) + (evt.desc.length > 80 ? '...' : '') : '无描述'}</div>
                </div>
            `;
        });
        if (chapterData.events.length > 5) {
            html += `<div style="text-align: center; color: #888; font-size: 11px;">还有 ${chapterData.events.length - 5} 个事件...</div>`;
        }
        html += '</div>';
    }

    detail.innerHTML = html;
}

function updateVolumeStats(volume) {
    const data = timelineData[volume];
    if (!data) return;

    const stats = { battle: 0, conspiracy: 0, daily: 0, emotion: 0 };
    
    if (data.events) {
        data.events.forEach(e => {
            const t = e.type || '日常';
            if (t === '战斗') stats.battle++;
            else if (t === '阴谋') stats.conspiracy++;
            else if (t === '日常') stats.daily++;
            else if (t === '情感') stats.emotion++;
        });
    }

    const statsDiv = document.getElementById('volume-stats');
    statsDiv.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; text-align: center;">
            <div style="background: rgba(199,91,91,0.1); padding: 10px; border-radius: 8px;">
                <div style="font-size: 20px; color: #c75b5b; font-weight: 700;">${stats.battle}</div>
                <div style="font-size: 11px; color: #888;">战斗</div>
            </div>
            <div style="background: rgba(154,106,212,0.1); padding: 10px; border-radius: 8px;">
                <div style="font-size: 20px; color: #9a6ad4; font-weight: 700;">${stats.conspiracy}</div>
                <div style="font-size: 11px; color: #888;">阴谋</div>
            </div>
            <div style="background: rgba(212,165,116,0.1); padding: 10px; border-radius: 8px;">
                <div style="font-size: 20px; color: #d4a574; font-weight: 700;">${stats.daily}</div>
                <div style="font-size: 11px; color: #888;">日常</div>
            </div>
            <div style="background: rgba(90,154,143,0.1); padding: 10px; border-radius: 8px;">
                <div style="font-size: 20px; color: #5a9a8f; font-weight: 700;">${stats.emotion}</div>
                <div style="font-size: 11px; color: #888;">情感</div>
            </div>
        </div>
        <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #2a2a3a;">
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #888;">
                <span>总事件: ${data.events?.length || 0}</span>
                <span>角色: ${data.meta?.characters_count || 0}</span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #888; margin-top: 4px;">
                <span>地点: ${data.meta?.locations_count || 0}</span>
                <span>场景: ${data.meta?.scenes_count || 0}</span>
            </div>
        </div>
    `;
}

function initTimelineFilters() {
    const container = document.getElementById('timeline-type-filters');
    if (!container) return;
    
    container.querySelectorAll('.filter-tag').forEach(tag => {
        tag.addEventListener('click', function() {
            container.querySelectorAll('.filter-tag').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            const type = this.dataset.type;
            filterTimelineByType(type);
        });
    });
}

function filterTimelineByType(type) {
    const chapters = document.querySelectorAll('.timeline-chapter');
    chapters.forEach(ch => {
        if (type === 'all') {
            ch.style.display = '';
            return;
        }
        const hasType = ch.querySelector(`.timeline-event-tag.${type === '战斗' ? 'battle' : type === '阴谋' ? 'conspiracy' : type === '情感' ? 'emotion' : 'daily'}`);
        ch.style.display = hasType ? '' : 'none';
    });
}

function initTimelineVolumeSelect() {
    const select = document.getElementById('timeline-volume-select');
    if (!select) return;
    
    select.addEventListener('change', async function() {
        const volume = this.value;
        if (volume === 'all') {
            // 加载所有卷
            for (let i = 1; i <= 28; i++) {
                if (!timelineData[i]) await loadTimelineData(i.toString());
            }
            // 合并显示
            renderAllVolumes();
        } else {
            if (!timelineData[volume]) await loadTimelineData(volume);
            renderTimeline(volume);
            updateVolumeStats(volume);
        }
    });
}

function renderAllVolumes() {
    const wrapper = document.getElementById('timeline-wrapper');
    wrapper.innerHTML = '';
    
    for (let i = 1; i <= 28; i++) {
        const data = timelineData[i];
        if (!data) continue;
        
        const volHeader = document.createElement('div');
        volHeader.style.cssText = 'padding: 15px; margin: 20px 0 10px -40px; background: linear-gradient(90deg, rgba(212,165,116,0.2), transparent); border-left: 4px solid #d4a574;';
        volHeader.innerHTML = `<div style="font-size: 16px; font-weight: 700; color: #d4a574;">第${i}卷</div>`;
        wrapper.appendChild(volHeader);
        
        renderTimeline(i.toString());
    }
}

function resetTimelineView() {
    document.getElementById('timeline-container').scrollTop = 0;
    document.querySelectorAll('.timeline-chapter').forEach(el => {
        el.style.display = '';
        el.classList.remove('active');
    });
    document.getElementById('chapter-detail').innerHTML = '点击左侧时间轴节点查看章节详情';
}
