const axios = require('axios');
const cheerio = require('cheerio');

async function test() {
    const url = 'https://www.biblegateway.com/passage/?search=Matthew+1&version=CHR';
    const res = await axios.get(url, {
        headers: { 'User-Agent': 'Mozilla/5.0' }
    });
    const $ = cheerio.load(res.data);

    // Select inside .passage-text or .passage-content
    // Try to find verses.

    console.log('Searching in .passage-content...');
    $('.passage-content .text').each((i, el) => {
        if (i < 5) {
            console.log('--- Element', i, '---');
            // Remove sups
            const $el = cheerio.load($(el).html()); // Hacky, better to use $(el).clone()
            // But let's just inspect raw HTML first
            console.log($(el).html());
            console.log('Class:', $(el).attr('class'));
        }
    });
}

test();
