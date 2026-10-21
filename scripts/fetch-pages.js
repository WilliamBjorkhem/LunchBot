const { chromium } = require("playwright");
const fs = require("fs");

const restaurants = JSON.parse(
  fs.readFileSync("restaurants.json", "utf8")
);

async function run() {
  const browser = await chromium.launch();

  for (const restaurant of restaurants) {
    const page = await browser.newPage();

    console.log(`Fetching ${restaurant.url}`);

    await page.goto(restaurant.url, {
      waitUntil: "domcontentloaded",
      timeout: 60000
    });

    await page.waitForTimeout(5000);

    const html = await page.content();

    fs.mkdirSync(
      `data/${restaurant.name}`,
      { recursive: true }
    );

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

    fs.writeFileSync(
      `data/${restaurant.name}/assets.json`,
      JSON.stringify(assets, null, 2)
    );

    console.log(
      `${restaurant.name}: found ${assets.length} assets`
    );
  }

  await browser.close();
}

run();
