const fs = require('fs');
const path = require('path');

const VOLUMES_DIR = path.join(__dirname, 'volumes');
const FOOTPRINT_FILE = path.join(__dirname, 'footprint_v2.json');

function readJSON(filePath) {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function writeJSON(filePath, data) {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
}

function getVolumeName(volume) {
    const volumeNames = [
        '', '第一卷', '第二卷', '第三卷', '第四卷', '第五卷',
        '第六卷', '第七卷', '第八卷', '第九卷', '第十卷',
        '第十一卷', '第十二卷', '第十三卷', '第十四卷', '第十五卷',
        '第十六卷', '第十七卷', '第十八卷', '第十九卷', '第二十卷',
        '第二十一卷', '第二十二卷', '第二十三卷', '第二十四卷', '第二十五卷',
        '第二十六卷', '第二十七卷', '第二十八卷'
    ];
    return volumeNames[volume] || `第${volume}卷`;
}

function chineseToNumber(chinese) {
    const numMap = { '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10 };
    let num = 0;
    for (const char of chinese) {
        if (numMap[char] !== undefined) {
            num = num * 10 + numMap[char];
        }
    }
    return num || 0;
}

function parseChapterNum(chapterStr) {
    if (!chapterStr) return 0;
    if (typeof chapterStr === 'number') return chapterStr;

    const match = chapterStr.match(/第(\d+)回/);
    if (match) return parseInt(match[1]);

    const chineseMatch = chapterStr.match(/第([零一二三四五六七八九十]+)回/);
    if (chineseMatch) return chineseToNumber(chineseMatch[1]);

    return 0;
}

function makeLookupKey(volume, chapterStr) {
    const chapterNum = parseChapterNum(chapterStr);
    if (chapterNum === 0) {
        return `${volume}_楔子`;
    }
    return `${volume}_第${chapterNum}回`;
}

function convertNewFormatScene(scene, volume) {
    const chapterNum = parseChapterNum(scene.chapter);
    const chapterStr = chapterNum === 0 ? '楔子' : `第${chapterNum}回`;
    const locationName = scene.location || scene.location_name || '';

    return [{
        volume: volume,
        chapter: chapterStr,
        full_name: `第${volume}卷 ${scene.chapter}`,
        location_name: locationName,
        characters: scene.characters || [],
        events: [{
            id: scene.id || `evt_${volume}_${chapterNum}`,
            type: scene.title ? '场景' : '事件',
            summary: scene.description || scene.summary || scene.name || '',
            outcome: '',
            participants: scene.characters || []
        }]
    }];
}

function convertSimpleScene(scene, volume, sceneIndex, chapterStartNum) {
    const chapterNum = chapterStartNum + sceneIndex;
    const chapterStr = `第${chapterNum}回`;
    const locationName = scene.location || scene.location_name || '';

    return [{
        volume: volume,
        chapter: chapterStr,
        full_name: `第${volume}卷 ${chapterStr}`,
        location_name: locationName,
        characters: scene.characters || [],
        events: [{
            id: scene.id ? `evt_${volume}_${scene.id}` : `evt_${volume}_${chapterNum}`,
            type: scene.title ? '场景' : '事件',
            summary: scene.description || scene.summary || scene.name || '',
            outcome: '',
            participants: scene.characters || []
        }]
    }];
}

function getChapterStartFromMeta(meta) {
    if (!meta || !meta.chapter_range) return 1;
    const match = meta.chapter_range.match(/第(\d+)/);
    if (match) return parseInt(match[1]);
    return 1;
}

function main() {
    console.log('开始更新 footprint_v2.json...');

    const footprint = readJSON(FOOTPRINT_FILE);
    const existingVolumeSet = new Set(footprint.chapters.map(c => c.volume));
    console.log(`现有章节卷数: ${[...existingVolumeSet].sort((a,b)=>a-b).join(', ')}`);

    const volumeFiles = fs.readdirSync(VOLUMES_DIR)
        .filter(f => f.match(/^volume_\d+\.json$/))
        .sort((a, b) => {
            const numA = parseInt(a.match(/\d+/)[0]);
            const numB = parseInt(b.match(/\d+/)[0]);
            return numA - numB;
        });

    let newChapterEntries = [];
    let scenesCount = 0;
    let processedVols = [];

    for (const file of volumeFiles) {
        const volumeNum = parseInt(file.match(/\d+/)[0]);
        const volumeData = readJSON(path.join(VOLUMES_DIR, file));
        const volumeName = getVolumeName(volumeNum);

        if (existingVolumeSet.has(volumeNum)) {
            console.log(`跳过第${volumeNum}卷 (已存在)`);
            continue;
        }

        console.log(`处理第${volumeNum}卷...`);

        if (!volumeData.scenes || !Array.isArray(volumeData.scenes)) {
            console.log(`  第${volumeNum}卷没有 scenes 数组，跳过`);
            continue;
        }

        const scenes = volumeData.scenes;
        if (scenes.length === 0) continue;

        const firstScene = scenes[0];
        const hasLocationId = firstScene.location_id !== undefined;
        const hasChapterString = typeof firstScene.chapter === 'string' && firstScene.chapter.includes('回');
        const hasChapterNumber = typeof firstScene.chapter === 'number';
        const hasChapterField = firstScene.chapter !== undefined;

        let format = 'unknown';
        if (hasLocationId && firstScene.chapters) {
            format = 'old';
        } else if (hasChapterString) {
            format = 'new_string';
        } else if (hasChapterNumber) {
            format = 'new_number';
        } else if (hasChapterField === false && firstScene.id !== undefined) {
            format = 'simple';
        }

        console.log(`  格式: ${format}, scenes数量: ${scenes.length}`);

        let chapterStart = getChapterStartFromMeta(volumeData.meta);
        console.log(`  章节起始号: ${chapterStart}`);

        for (let i = 0; i < scenes.length; i++) {
            const scene = scenes[i];
            let entries = [];

            if (format === 'old') {
                console.log(`  警告: 第${volumeNum}卷使用旧格式但未被处理`);
                continue;
            } else if (format === 'new_string' || format === 'new_number') {
                entries = convertNewFormatScene(scene, volumeNum);
            } else if (format === 'simple') {
                entries = convertSimpleScene(scene, volumeNum, i, chapterStart - 1);
            }

            for (const entry of entries) {
                newChapterEntries.push(entry);
                scenesCount++;
            }
        }
        processedVols.push(volumeNum);
    }

    footprint.chapters = [...footprint.chapters, ...newChapterEntries];

    const newChapterLookup = {};
    for (let i = 0; i < footprint.chapters.length; i++) {
        const chapter = footprint.chapters[i];
        const volume = chapter.volume;
        const chapterStr = chapter.chapter;
        const lookupKey = makeLookupKey(volume, chapterStr);
        const chapterNum = chapterStr.includes('楔子') ? 0 : parseChapterNum(chapterStr);

        newChapterLookup[lookupKey] = {
            index: i,
            reader_volume: volume,
            reader_chapter: chapterNum
        };
    }
    footprint.chapter_lookup = newChapterLookup;

    footprint.meta.total_chapters = footprint.chapters.length;
    footprint.meta.total_locations = Object.keys(footprint.locations).length;

    console.log(`\n更新统计:`);
    console.log(`  处理了 ${processedVols.length} 卷: ${processedVols.join(', ')}`);
    console.log(`  新增 ${newChapterEntries.length} 个章节条目`);
    console.log(`  更新后总章节数: ${footprint.chapters.length}`);
    console.log(`  chapter_lookup 条目数: ${Object.keys(footprint.chapter_lookup).length}`);

    writeJSON(FOOTPRINT_FILE, footprint);
    console.log('\n更新完成！');
}

main();