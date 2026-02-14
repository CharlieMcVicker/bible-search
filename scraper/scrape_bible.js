const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');
const path = require('path');

const books = [
    // Old Testament (Commented out for NT run)
    /*
    { name: "Genesis", chapters: 50 },
    { name: "Exodus", chapters: 40 },
    { name: "Leviticus", chapters: 27 },
    { name: "Numbers", chapters: 36 },
    { name: "Deuteronomy", chapters: 34 },
    { name: "Joshua", chapters: 24 },
    { name: "Judges", chapters: 21 },
    { name: "Ruth", chapters: 4 },
    { name: "1 Samuel", chapters: 31 },
    { name: "2 Samuel", chapters: 24 },
    { name: "1 Kings", chapters: 22 },
    { name: "2 Kings", chapters: 25 },
    { name: "1 Chronicles", chapters: 29 },
    { name: "2 Chronicles", chapters: 36 },
    { name: "Ezra", chapters: 10 },
    { name: "Nehemiah", chapters: 13 },
    { name: "Esther", chapters: 10 },
    { name: "Job", chapters: 42 },
    { name: "Psalms", chapters: 150 },
    { name: "Proverbs", chapters: 31 },
    { name: "Ecclesiastes", chapters: 12 },
    { name: "Song of Solomon", chapters: 8 },
    { name: "Isaiah", chapters: 66 },
    { name: "Jeremiah", chapters: 52 },
    { name: "Lamentations", chapters: 5 },
    { name: "Ezekiel", chapters: 48 },
    { name: "Daniel", chapters: 12 },
    { name: "Hosea", chapters: 14 },
    { name: "Joel", chapters: 3 },
    { name: "Amos", chapters: 9 },
    { name: "Obadiah", chapters: 1 },
    { name: "Jonah", chapters: 4 },
    { name: "Micah", chapters: 7 },
    { name: "Nahum", chapters: 3 },
    { name: "Habakkuk", chapters: 3 },
    { name: "Zephaniah", chapters: 3 },
    { name: "Haggai", chapters: 2 },
    { name: "Zechariah", chapters: 14 },
    { name: "Malachi", chapters: 4 },
    */
    // New Testament
    { name: "Matthew", chapters: 28 },
    { name: "Mark", chapters: 16 },
    { name: "Luke", chapters: 24 },
    { name: "John", chapters: 21 },
    { name: "Acts", chapters: 28 },
    { name: "Romans", chapters: 16 },
    { name: "1 Corinthians", chapters: 16 },
    { name: "2 Corinthians", chapters: 13 },
    { name: "Galatians", chapters: 6 },
    { name: "Ephesians", chapters: 6 },
    { name: "Philippians", chapters: 4 },
    { name: "Colossians", chapters: 4 },
    { name: "1 Thessalonians", chapters: 5 },
    { name: "2 Thessalonians", chapters: 3 },
    { name: "1 Timothy", chapters: 6 },
    { name: "2 Timothy", chapters: 4 },
    { name: "Titus", chapters: 3 },
    { name: "Philemon", chapters: 1 },
    { name: "Hebrews", chapters: 13 },
    { name: "James", chapters: 5 },
    { name: "1 Peter", chapters: 5 },
    { name: "2 Peter", chapters: 3 },
    { name: "1 John", chapters: 5 },
    { name: "2 John", chapters: 1 },
    { name: "3 John", chapters: 1 },
    { name: "Jude", chapters: 1 },
    { name: "Revelation", chapters: 22 }
];

const versions = ['KJV', 'WEB', 'CHR']; // Added CHR (Cherokee NT) back for New Testament

async function fetchChapter(book, chapter, version) {
    const url = `https://www.biblegateway.com/passage/?search=${encodeURIComponent(book)}+${chapter}&version=${version}`;
    try {
        const response = await axios.get(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            timeout: 10000 
        });
        const $ = cheerio.load(response.data);
        const verses = {};

        // Find the main text container
        const passageContent = $('.passage-content');
        if (!passageContent.length) {
            console.warn(`    Warning: No content found for ${book} ${chapter} (${version})`);
            return {};
        }

        // Iterate over text elements
        // Strategy: 
        // 1. Identify verse start by .versenum or .chapternum
        // 2. Extract text, cleaning up footnotes/crossrefs
        
        passageContent.find('.text').each((i, el) => {
            const $el = $(el);
            
            // Get verse number
            let verseNum = $el.find('.versenum').text().trim();
            
            // Handle chapter start (e.g. "1" or "18" in .chapternum class)
            // This usually indicates Verse 1
            if (!verseNum && $el.find('.chapternum').length > 0) {
                verseNum = "1";
            }
            
            // If no verse number found in this element, it might be a continuation of the previous verse 
            // OR it's just some other text. 
            // However, BibleGateway usually puts each verse in a separate element with class 'text'.
            // Sometimes multiple 'text' elements belong to the same verse (e.g. poetry).
            // But we need to be careful not to overwrite or lose data.
            
            // If verseNum is present, we start a new verse entry.
            // If not, we might append to the last verse?
            // Checking the class list might help: "text Book-Ch-Verse"
            const classList = $el.attr('class') || '';
            const match = classList.match(/text [^\s]+-(\d+)-(\d+)/); // strict pattern? 
            // Classes are like "text Gen-1-1" or "text 1Cor-1-1"
            
            // If we can't find a verse number in the text, try extracting from class
            if (!verseNum && match) {
               verseNum = match[2]; // The verse part
            }

            if (!verseNum) {
                // If still no verse number, maybe check if it's a "woe" or "selah" or title?
                // For now, skip if we can't identify.
                return;
            }

            // Clean up text
            const $clone = $el.clone();
            $clone.find('.versenum, .chapternum, .crossreference, .footnote, .footnotes').remove();
            
            // Also remove headers if they are inside (usually they are outside .text)
            
            let text = $clone.text().replace(/\s+/g, ' ').trim();
            
            if (verses[verseNum]) {
                verses[verseNum] += " " + text;
            } else {
                verses[verseNum] = text;
            }
        });

        return verses;

    } catch (error) {
        console.error(`    Error fetching ${book} ${chapter} (${version}):`, error.message);
        return {};
    }
}

async function scrape() {
    const dataDir = path.join(__dirname, 'data');
    if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir);

    let startProcessing = false;
    for (const book of books) {
        if (book.name === "Luke") startProcessing = true;
        if (!startProcessing) continue;

        const bookDir = path.join(dataDir, book.name);
        if (!fs.existsSync(bookDir)) fs.mkdirSync(bookDir);

        console.log(`Processing ${book.name} (${book.chapters} chapters)...`);

        for (let chapter = 1; chapter <= book.chapters; chapter++) {
            const outputFile = path.join(bookDir, `${chapter}.json`);
            
            // Overwriting enabled for repull
            // if (fs.existsSync(outputFile)) {
            //     // console.log(`  Skipping ${book.name} ${chapter} (already exists)`);
            //     continue;
            // }

            console.log(`  Fetching ${book.name} ${chapter}...`);
            
            // Fetch all versions in parallel for this chapter
            const promises = versions.map(v => fetchChapter(book.name, chapter, v));
            const results = await Promise.all(promises);
            
            const kjv = results[0];
            const web = results[1];
            
            // Validate we got something
            if (Object.keys(kjv).length === 0 && Object.keys(web).length === 0) {
                console.error(`  FAILED to get data for ${book.name} ${chapter}`);
                continue; 
            }

            // Align
            const allVerses = new Set([
                ...Object.keys(kjv),
                ...Object.keys(web),
                ...Object.keys(results[2] || {})
            ]);
            
            const sortedVerses = Array.from(allVerses).sort((a, b) => parseInt(a) - parseInt(b));
            
            const chr = results[2] || {};

            const aligned = sortedVerses.map(v => ({
                verse: v,
                kjv: kjv[v] || "",
                web: web[v] || "",
                chr: chr[v] || ""
            }));
            
            fs.writeFileSync(outputFile, JSON.stringify(aligned, null, 2));
            
            // Rate limiting
            await new Promise(r => setTimeout(r, 500));
        }
    }
    console.log("Scraping complete!");
}

scrape();