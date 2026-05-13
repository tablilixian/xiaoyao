const fs = require('fs');
const path = require('path');

const FOOTPRINT_FILE = path.join(__dirname, 'footprint_v2.json');

function readJSON(filePath) {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function main() {
    console.log('分析 chapters 数据结构...\n');

    const footprint = readJSON(FOOTPRINT_FILE);
    const chapters = footprint.chapters;

    const chapterMap = new Map();
    const duplicates = [];

    for (let i = 0; i < chapters.length; i++) {
        const ch = chapters[i];
        const key = `${ch.volume}_${ch.chapter}_${ch.location_name}`;

        if (chapterMap.has(key)) {
            duplicates.push({
                index: i,
                existingIndex: chapterMap.get(key),
                key: key,
                chapter: ch
            });
        } else {
            chapterMap.set(key, i);
        }
    }

    console.log(`总 chapters 条目数: ${chapters.length}`);
    console.log(`唯一条目数 (volume+chapter+location): ${chapterMap.size}`);
    console.log(`重复条目数: ${duplicates.length}\n`);

    if (duplicates.length > 0) {
        console.log('部分重复条目:');
        for (let i = 0; i < Math.min(5, duplicates.length); i++) {
            const d = duplicates[i];
            console.log(`  [${d.index}] ${d.chapter.full_name} @ ${d.chapter.location_name}`);
            console.log(`       已有位置: [${d.existingIndex}]`);
        }
    }

    const volumeChapterMap = new Map();
    for (let i = 0; i < chapters.length; i++) {
        const ch = chapters[i];
        const key = `${ch.volume}_${ch.chapter}`;
        if (!volumeChapterMap.has(key)) {
            volumeChapterMap.set(key, []);
        }
        volumeChapterMap.get(key).push(i);
    }

    console.log(`\n按 volume+chapter 分组后唯一卷章节数: ${volumeChapterMap.size}`);

    const multipleScenes = [];
    for (const [key, indices] of volumeChapterMap) {
        if (indices.length > 1) {
            multipleScenes.push({ key, count: indices.length });
        }
    }

    console.log(`有多场景的卷章节数: ${multipleScenes.length}`);
    if (multipleScenes.length > 0) {
        console.log('部分多场景条目:');
        for (let i = 0; i < Math.min(5, multipleScenes.length); i++) {
            const m = multipleScenes[i];
            console.log(`  ${m.key}: ${m.count} 个场景`);
        }
    }
}

main();