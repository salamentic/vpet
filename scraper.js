// Enhanced Digimon World DS Sprite Scraper
// This script requires Node.js with the following packages:
// npm install axios cheerio fs path

const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');
const path = require('path');
const { promisify } = require('util');
const writeFileAsync = promisify(fs.writeFile);
const mkdirAsync = promisify(fs.mkdir);

// Base URLs for the sprite resource
const baseUrl = 'https://www.spriters-resource.com';
const targetUrl = 'https://www.spriters-resource.com/ds_dsi/dgmnworldds/';

// Configuration
const config = {
  delay: 1000, // Delay between requests (ms) to avoid overwhelming the server
  downloadImages: true, // Set to false to skip image downloads during testing
  categorize: true, // Create folder structure based on Digimon categories
  saveMetadata: true, // Save metadata about each sprite
  includeID: true, // Include sheet ID in the filename
  retries: 3, // Number of retries for failed downloads
  retryDelay: 3000, // Delay between retries (ms)
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
  maxConcurrent: 1, // Maximum number of concurrent downloads (keep low to avoid overloading the server)
  debugMode: true // Enable additional logging for debugging
};

// Create directories for saving sprites
const outputDir = path.join(__dirname, 'digimon_sprites');

// Helper function to create a delay
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Helper function to sanitize filenames
const sanitizeFilename = (name) => {
  return name
    .replace(/[/\\?%*:|"<>]/g, '-') // Replace invalid characters
    .replace(/\s+/g, '_')           // Replace spaces with underscores
    .trim();
};

// Helper function to extract section names from the HTML
const extractSections = ($) => {
  const sections = [];
  $('.section').each((i, element) => {
    const name = $(element).find('.sect-name').attr('title');
    if (name) {
      sections.push({
        name,
        element: $(element)
      });
    }
  });
  return sections;
};

// Parse individual sheet page to get the actual sprite image URL
async function getSheetImageUrl(sheetUrl) {
  try {
    console.log(`Fetching sheet page: ${sheetUrl}`);
    const response = await axios.get(sheetUrl, {
      headers: { 
        'User-Agent': config.userAgent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
      }
    });
    
    // Log status code for debugging
    if (config.debugMode) {
      console.log(`Status code: ${response.status} for ${sheetUrl}`);
    }
    
    const $ = cheerio.load(response.data);
    
    // Based on the second HTML you provided, the image should be in #sheet-container img
    let imgSrc = $('#sheet-container img').attr('src');
    
    if (config.debugMode) {
      // Output the value found for debugging
      console.log(`Found image src: ${imgSrc || 'null'}`);
      
      // Check if the element exists at all
      console.log(`#sheet-container exists: ${$('#sheet-container').length > 0}`);
      console.log(`#sheet-container img exists: ${$('#sheet-container img').length > 0}`);
      
      // Check for any images on the page
      const allImages = $('img');
      console.log(`Total images found on page: ${allImages.length}`);
      
      // Print the first few images for debugging
      allImages.slice(0, 3).each((i, el) => {
        console.log(`Image ${i+1}: ${$(el).attr('src')}`);
      });
    }
    
    // If the image source was found, use it
    if (imgSrc) {
      // Some URLs are relative, ensure we have the full URL
      return imgSrc.startsWith('http') ? imgSrc : baseUrl + imgSrc;
    }
    
    // If no image src found, look for a download link
    const downloadLink = $('a[href^="/download/"]').attr('href');
    if (downloadLink) {
      // Extract the sheet ID from the download link
      const sheetIdMatch = downloadLink.match(/\/download\/(\d+)/);
      if (sheetIdMatch && sheetIdMatch[1]) {
        const sheetId = sheetIdMatch[1];
        console.log(`Using direct download link for sheet ID: ${sheetId}`);
        // Construct the direct download URL
        return `${baseUrl}${downloadLink}`;
      }
    }
    
    // If still no image found, check for a fullview link
    const fullviewLink = $('a[href^="/fullview/"]').attr('href');
    if (fullviewLink) {
      // Follow the fullview link to get the image
      const fullviewUrl = fullviewLink.startsWith('http') ? fullviewLink : baseUrl + fullviewLink;
      console.log(`Following fullview link: ${fullviewUrl}`);
      
      // Add a small delay before making the next request
      await sleep(config.delay / 2);
      
      const fullviewResponse = await axios.get(fullviewUrl, {
        headers: { 'User-Agent': config.userAgent }
      });
      const $fullview = cheerio.load(fullviewResponse.data);
      imgSrc = $fullview('#fullview-container img').attr('src');
      
      if (imgSrc) {
        return imgSrc.startsWith('http') ? imgSrc : baseUrl + imgSrc;
      }
    }
    
    // If we still can't find the image, extract the sheet ID from the URL
    const sheetIdMatch = sheetUrl.match(/\/sheet\/(\d+)\//);
    if (sheetIdMatch && sheetIdMatch[1]) {
      const sheetId = sheetIdMatch[1];
      console.log(`Falling back to direct download with sheet ID: ${sheetId}`);
      return `${baseUrl}/download/${sheetId}/`;
    }
    
    console.error(`No image found on sheet page: ${sheetUrl}`);
    
    // Debug: Save the HTML for inspection if in debug mode
    if (config.debugMode) {
      const debugFilename = path.join(outputDir, `debug_${Date.now()}.html`);
      await writeFileAsync(debugFilename, response.data);
      console.log(`Saved HTML for debugging to: ${debugFilename}`);
    }
    
    return null;
  } catch (error) {
    console.error(`Error fetching sheet page ${sheetUrl}: ${error.message}`);
    return null;
  }
}

// Download an image with retries
async function downloadImage(url, filename, retryCount = 0) {
  if (config.debugMode) {
    console.log(`Attempting to download: ${url}`);
  }
  
  try {
    const response = await axios({
      url,
      method: 'GET',
      responseType: 'arraybuffer',
      headers: { 
        'User-Agent': config.userAgent,
        'Referer': baseUrl,
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache'
      },
      timeout: 30000 // 30 second timeout
    });
    
    // Check if we got an actual image (content-type should be image/*)
    const contentType = response.headers['content-type'];
    if (!contentType || !contentType.startsWith('image/')) {
      if (config.debugMode) {
        console.warn(`Response for ${url} is not an image. Content-Type: ${contentType}`);
        // Save the response for debugging
        await writeFileAsync(`${filename}.debug`, response.data);
      }
      
      // If it's HTML, we may have been redirected to an error page
      if (contentType && contentType.includes('html')) {
        throw new Error(`Received HTML instead of an image. Likely an error page.`);
      }
    }
    
    await writeFileAsync(filename, response.data);
    console.log(`Downloaded: ${filename}`);
    return true;
  } catch (error) {
    if (retryCount < config.retries) {
      console.log(`Retry ${retryCount + 1}/${config.retries} for ${url}: ${error.message}`);
      await sleep(config.retryDelay);
      return downloadImage(url, filename, retryCount + 1);
    } else {
      console.error(`Failed to download ${url} after ${config.retries} attempts: ${error.message}`);
      return false;
    }
  }
}

// Process a sprite sheet entry
async function processSheetEntry(entry, category) {
  const { title, url, iconUrl, sheetId } = entry;
  
  // Create category directory if categorizing
  let targetDir = outputDir;
  if (config.categorize && category) {
    targetDir = path.join(outputDir, sanitizeFilename(category));
    if (!fs.existsSync(targetDir)) {
      await mkdirAsync(targetDir, { recursive: true });
    }
  }
  
  // Fetch submitter information from the sprite page
  let submitter = "Unknown";
  try {
    const pageResponse = await axios.get(url, {
      headers: { 
        'User-Agent': config.userAgent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
      }
    });
    
    const $page = cheerio.load(pageResponse.data);
    
    // Find the submitter row
    $page('.display.altrow tr').each((i, row) => {
      const label = $page(row).find('td').first().text().trim();
      if (label === 'Submitter') {
        // Extract submitter name
        const submitterCell = $page(row).find('td').last();
        submitter = submitterCell.text().trim();
        
        // Get just the username - remove any extra info
        if (submitter.includes('/')) {
          submitter = submitter.split('/')[0].trim();
        }
        
        if (config.debugMode) {
          console.log(`Found submitter: ${submitter}`);
        }
      }
    });
  } catch (error) {
    console.warn(`Could not fetch submitter info: ${error.message}`);
  }
  
  // Build filename with optional ID and submitter
  let filename = sanitizeFilename(title);
  if (config.includeID && sheetId) {
    filename = `${sheetId}_${filename}`;
  }
  
  // Add submitter to filename
  filename = `${filename}_by_${sanitizeFilename(submitter)}`;
  
  // First, save the icon image if available
  if (iconUrl && config.downloadImages) {
    const iconPath = path.join(targetDir, `${filename}_icon.png`);
    await downloadImage(iconUrl, iconPath);
  }
  
  // Get the full sheet image URL
  let fullImageUrl = null;
  let downloadSuccess = false;
  
  if (config.downloadImages) {
    // Try to get the image URL
    fullImageUrl = await getSheetImageUrl(url);
    
    if (fullImageUrl) {
      const imagePath = path.join(targetDir, `${filename}.png`);
      downloadSuccess = await downloadImage(fullImageUrl, imagePath);
      
      // If download failed with the first method, try direct download
      if (!downloadSuccess && sheetId) {
        console.log(`Trying direct download for sheet ID: ${sheetId}`);
        const directUrl = `${baseUrl}/download/${sheetId}/`;
        downloadSuccess = await downloadImage(directUrl, imagePath);
      }
    } else if (sheetId) {
      // Try direct download as a fallback
      console.log(`Trying direct download for sheet ID: ${sheetId}`);
      const directUrl = `${baseUrl}/download/${sheetId}/`;
      const imagePath = path.join(targetDir, `${filename}.png`);
      downloadSuccess = await downloadImage(directUrl, imagePath);
    }
  }
  
  // Return metadata about this sheet
  return {
    id: sheetId,
    title,
    url,
    category,
    submitter,
    iconUrl,
    fullImageUrl,
    downloadSuccess,
    timestamp: new Date().toISOString()
  };
}

// Extract information from a sprite icon container
function extractSheetInfo($, container) {
  const $container = $(container);
  const $link = $container.parent();
  const href = $link.attr('href') || '';
  
  // Extract the sheet ID from href using regex
  const sheetIdMatch = href.match(/\/sheet\/(\d+)\//);
  const sheetId = sheetIdMatch ? sheetIdMatch[1] : null;
  
  // Extract the title and icon URL
  const title = $container.find('.iconheadertext').text().trim();
  const iconImg = $container.find('.iconbody img');
  const iconUrl = iconImg.attr('src');
  const fullIconUrl = iconUrl ? (iconUrl.startsWith('http') ? iconUrl : baseUrl + iconUrl) : null;
  
  return {
    title,
    url: href.startsWith('http') ? href : baseUrl + href,
    iconUrl: fullIconUrl,
    sheetId
  };
}

// Main function to scrape all Digimon sprites
async function scrapeDigimonSprites() {
  try {
    console.log(`Starting enhanced Digimon World DS sprite scraper...`);
    
    // Create the output directory if it doesn't exist
    if (!fs.existsSync(outputDir)) {
      await mkdirAsync(outputDir, { recursive: true });
    }
    
    // Fetch the main page
    console.log(`Fetching main page: ${targetUrl}`);
    const response = await axios.get(targetUrl, {
      headers: { 'User-Agent': config.userAgent }
    });
    
    const $ = cheerio.load(response.data);
    const sections = extractSections($);
    
    console.log(`Found ${sections.length} sections`);
    
    // Store all sprite data for metadata
    const allSprites = [];
    const successCount = {total: 0, success: 0};
    
    // Process each section
    for (const [sectionIndex, section] of sections.entries()) {
      const sectionName = section.name;
      console.log(`Processing section ${sectionIndex + 1}/${sections.length}: ${sectionName}`);
      
      // Find the next updatesheeticons div after this section
      const iconsContainer = section.element.next('.updatesheeticons');
      
      // Find all sprite containers in this section
      const spriteContainers = iconsContainer.find('.iconcontainer');
      console.log(`Found ${spriteContainers.length} sprites in section ${sectionName}`);
      
      // Process each sprite in this section
      for (const [spriteIndex, container] of Array.from(spriteContainers).entries()) {
        const sheetInfo = extractSheetInfo($, container);
        
        console.log(`Processing sprite ${spriteIndex + 1}/${spriteContainers.length}: ${sheetInfo.title}`);
        
        // Process the sprite and collect metadata
        const spriteData = await processSheetEntry(sheetInfo, sectionName);
        allSprites.push(spriteData);
        
        // Update success counters
        successCount.total++;
        if (spriteData.downloadSuccess) {
          successCount.success++;
        }
        
        // Delay between requests to avoid overwhelming the server
        if (spriteIndex < spriteContainers.length - 1) {
          await sleep(config.delay);
        }
      }
      
      // Additional delay between sections
      if (sectionIndex < sections.length - 1) {
        await sleep(config.delay * 2);
      }
      
      // Every 10 sections, provide a progress update
      if ((sectionIndex + 1) % 10 === 0 || sectionIndex === sections.length - 1) {
        console.log(`Progress: ${successCount.success}/${successCount.total} sprites successfully downloaded (${Math.round(successCount.success/successCount.total*100)}%)`);
      }
    }
    
    // Save metadata if enabled
    if (config.saveMetadata) {
      const metadata = {
        source: targetUrl,
        scrapeDate: new Date().toISOString(),
        totalSprites: allSprites.length,
        successfulDownloads: successCount.success,
        sprites: allSprites
      };
      
      await writeFileAsync(
        path.join(outputDir, 'metadata.json'),
        JSON.stringify(metadata, null, 2)
      );
      
      console.log(`Saved metadata to metadata.json`);
    }
    
    console.log(`Sprite scraping completed! Downloaded ${successCount.success}/${allSprites.length} sprites (${Math.round(successCount.success/allSprites.length*100)}% success rate).`);
    
  } catch (error) {
    console.error(`Error during scraping: ${error.message}`);
    console.error(error.stack);
  }
}

// Run the main function
scrapeDigimonSprites().catch(error => {
  console.error('An unhandled error occurred during scraping:', error);
  process.exit(1);
});
