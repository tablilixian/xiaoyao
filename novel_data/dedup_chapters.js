const fs = require('fs');
const path = require('path');

const FOOTPRINT_FILE = path.join(__dirname, 'footprint_v2.json');

function readJSON(filePath) {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function writeJSON(filePath, data) {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
}

function makeChapterKey(chapter) {
    return `${chapter.volume}_${chapter.chapter}_${chapter.location_name}`;
}

function main() {
    console.log('开始检查重复章节...');

    const footprint = readJSON(FOOTPRINT_FILE);
    const seen = new Set();
    const duplicates = [];
    const uniqueChapters = [];

    for (let i = 0; i < footprint.chapters.length; i++) {
        const chapter = footprint.chapters[i];
        const key = makeChapterKey(chapter);

        if (seen.has(key)) {
            duplicates.push({ index: i, key, chapter });
        } else {
            seen.add(key);
            uniqueChapters.push(chapter);
        }
    }

    console.log(`\n检查结果:`);
    console.log(`  原始章节数: ${footprint.chapters.length}`);
    console.log(`  重复章节数: ${duplicates.length}`);
    console.log(`  去重后章节数: ${uniqueChapters.length}`);

    if (duplicates.length > 0) {
        console.log(`\n部分重复条目:`);
        for (let i = 0; i < Math.min(10, duplicates.length); i++) {
            const d = duplicates[i];
            console.log(`  位置 ${d.index}: ${d.chapter.full_name} @ ${d.chapter.location_name}`);
        }
        if (duplicates.length > 10) {
            console.log(`  ... 还有 ${duplicates.length - 10} 个重复`);
        }

        footprint.chapters = uniqueChapters;

        const newChapterLookup = {};
        for (let i = 0; i < footprint.chapters.length; i++) {
            const chapter = footprint.chapters[i];
            const chapterNum = chapter.chapter.includes('楔子') ? 0 :
                parseInt(chapter.chapter.match(/第(\d+)回/)?.[1] || '0');
            const lookupKey = `${chapter.volume}_${chapterNum === 0 ? '楔子' : `第${chapterNum}回`}`;

            newChapterLookup[lookupKey] = {
                index: i,
                reader_volume: chapter.volume,
                reader_chapter: chapterNum
            };
        }

        footprint.chapter_lookup = newChapterLookup;
        footprint.meta.total_chapters = footprint.chapters.length;

        console.log(`\n更新后:`);
        console.log(`  chapters 数量: ${footprint.chapters.length}`);
        console.log(`  chapter_lookup 条目数: ${Object.keys(footprint.chapter_lookup).length}`);

        writeJSON(FOOTPRINT_FILE, footprint);
        console.log(`\n已保存更新！`);
    } else {
        console.log(`\n没有发现重复章节`);
    }
}

main();