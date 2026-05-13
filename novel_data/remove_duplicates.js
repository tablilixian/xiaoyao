const fs = require('fs');
const path = require('path');

const FOOTPRINT_FILE = path.join(__dirname, 'footprint_v2.json');

function readJSON(filePath) {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function writeJSON(filePath, data) {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
}

function main() {
    console.log('删除重复章节条目...\n');

    const footprint = readJSON(FOOTPRINT_FILE);
    const chapters = footprint.chapters;

    const seen = new Set();
    const uniqueChapters = [];
    let removedCount = 0;

    for (let i = 0; i < chapters.length; i++) {
        const ch = chapters[i];
        const key = `${ch.volume}_${ch.chapter}_${ch.location_name}`;

        if (seen.has(key)) {
            removedCount++;
        } else {
            seen.add(key);
            uniqueChapters.push(ch);
        }
    }

    console.log(`原始条目数: ${chapters.length}`);
    console.log(`删除重复数: ${removedCount}`);
    console.log(`去重后条目数: ${uniqueChapters.length}\n`);

    footprint.chapters = uniqueChapters;

    const newChapterLookup = {};
    for (let i = 0; i < footprint.chapters.length; i++) {
        const chapter = footprint.chapters[i];
        const chapterNum = chapter.chapter.includes('楔子') ? 0 :
            parseInt(chapter.chapter.match(/第(\d+)回/)?.[1] || '0');
        const lookupKey = `${chapter.volume}_${chapterNum === 0 ? '楔子' : `第${chapterNum}回`}`;

        if (!newChapterLookup[lookupKey]) {
            newChapterLookup[lookupKey] = {
                index: i,
                reader_volume: chapter.volume,
                reader_chapter: chapterNum
            };
        }
    }

    footprint.chapter_lookup = newChapterLookup;
    footprint.meta.total_chapters = footprint.chapters.length;

    console.log('更新 chapter_lookup...');
    console.log(`chapter_lookup 条目数: ${Object.keys(newChapterLookup).length}\n`);

    writeJSON(FOOTPRINT_FILE, footprint);
    console.log('更新完成！');
}

main();