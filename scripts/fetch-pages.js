const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const restaurants = JSON.parse(
  fs.readFileSync(
    path.join(__dirname, "restaurants.json"),
    "utf8"
  )
);

async function run() {
  const browser = await chromium.launch({
    headless: true
  });

  for (const restaurant of restaurants) {
    const outputDir = `data/${restaurant.name}`;

    fs.mkdirSync(outputDir, {
      recursive: true
    });

    const page = await browser.newPage();

    try {
      console.log(`Fetching ${restaurant.url}`);

      await page.goto(restaurant.url, {
        waitUntil: "domcontentloaded",
        timeout: 60000
      });

      await page.waitForTimeout(5000);

      const html = await page.content();

      fs.writeFileSync(
        `${outputDir}/page.html`,
        html
      );

      fs.writeFileSync(
        `${outputDir}/page_url.txt`,
        page.url()
      );

      await page.screenshot({
        path: `${outputDir}/page.png`,
        fullPage: true
      });

      const assets = await page.evaluate(() => {
        const urls = [];

        document.querySelectorAll("img").forEach(img => {
          if (img.src) {
            urls.push(img.src);
          }
        });

        document.querySelectorAll("a").forEach(a => {
          if (
            a.href &&
            a.href.match(/\.pdf($|\?)/i)
          ) {
            urls.push(a.href);
          }
        });

        return [...new Set(urls)];
      });

      fs.writeFileSync(
        `${outputDir}/assets.json`,
        JSON.stringify(
          assets,
          null,
          2
        )
      );

      console.log(
        `${restaurant.name}: found ${assets.length} assets`
      );
    } catch (err) {
      console.error(
        `Failed scraping ${restaurant.name}`
      );
      console.error(err);

      fs.writeFileSync(
        `${outputDir}/error.txt`,
        String(err)
      );
    } finally {
      await page.close();
    }
  }

  await browser.close();
}

run().catch(err => {
  console.error(err);
  process.exit(1);
});
