const { chromium } = require("playwright");
const fs = require("fs");

const restaurants = [
  {
    name: "mrbnme",
    url: "https://www.mrbnme.com/lunch"
  },
  {
    name: "ballstaviken",
    url: "https://www.sabis.se/restaurang-ballstaviken"
  }
];

async function run() {
  const browser = await chromium.launch();

  for (const restaurant of restaurants) {
    const page = await browser.newPage();

    await page.goto(restaurant.url, {
      waitUntil: 'domcontentloaded',
      timeout: 60000
    });

    await page.waitForTimeout(5000);

    const html = await page.content();

    fs.mkdirSync(`data/${restaurant.name}`, {
      recursive: true
    });

    fs.writeFileSync(
      `data/${restaurant.name}/page.html`,
      html
    );

    const assets = await page.evaluate(() => {
      const urls = [];

      document.querySelectorAll("img").forEach(img => {
        if (img.src) urls.push(img.src);
      });

      document.querySelectorAll("a").forEach(a => {
        if (a.href.match(/\.pdf($|\?)/i)) {
          urls.push(a.href);
        }
      });

      return urls;
    });

    console.log(`\n${restaurant.name} assets:`);
    for (const asset of assets) {
      console.log(asset);
    }

    fs.writeFileSync(
      `data/${restaurant.name}/assets.json`,
      JSON.stringify(assets, null, 2)
    );

    console.log(`${restaurant.name}: found ${assets.length} assets`);
  }

  await browser.close();
}

run();
