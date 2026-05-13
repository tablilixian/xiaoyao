const fs = require('fs');
const path = require('path');

const FOOTPRINT_FILE = path.join(__dirname, 'footprint_v2.json');

function readJSON(filePath) {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function writeJSON(filePath, data) {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
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

function main() {
    console.log('开始重建 chapter_lookup...');

    const footprint = readJSON(FOOTPRINT_FILE);

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

    const volumeCounts = {};
    for (const chapter of footprint.chapters) {
        const vol = chapter.volume;
        volumeCounts[vol] = (volumeCounts[vol] || 0) + 1;
    }

    console.log(`\n更新统计:`);
    console.log(`  chapters 数量: ${footprint.chapters.length}`);
    console.log(`  chapter_lookup 条目数: ${Object.keys(footprint.chapter_lookup).length}`);
    console.log(`  各卷章节数:`);
    for (let v = 1; v <= 28; v++) {
        if (volumeCounts[v]) {
            console.log(`    第${v}卷: ${volumeCounts[v]} 章`);
        }
    }

    writeJSON(FOOTPRINT_FILE, footprint);
    console.log('\n更新完成！');
}

main();