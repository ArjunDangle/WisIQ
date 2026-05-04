const fsSync = require('fs');
const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');
const vm = require('vm');
const cheerio = require('cheerio'); // Make sure to run: npm install cheerio

// --- 📁 DIRECTORY SETUP ---
const PROJECT_ROOT = __dirname;
const TARGET_DIR = path.join(PROJECT_ROOT, 'data', 'raw','product-categories');
const OUTPUT_DIR = path.join(PROJECT_ROOT, 'rag-docs', 'product-categories');

// --- 📊 DATA LOADERS ---
let firmwareData = {};
let certIconsData = {};
let productComparisonData = {};
let productComparisonIdentifiers = {};

function loadDocusaurusJs(filePath) {
    if (!fsSync.existsSync(filePath)) return null;
    let code = fsSync.readFileSync(filePath, 'utf8');
    code = code.replace(/import\s+.*?from\s+['"].*?['"];?/g, ''); 
    code = code.replace(/export\s+default\s+([a-zA-Z0-9_]+);?/g, 'extractedData = $1;'); 
    
    const sandbox = { extractedData: null };
    vm.createContext(sandbox);
    try {
        vm.runInContext(code, sandbox);
        return sandbox.extractedData;
    } catch (e) {
        console.warn(`⚠️ Sandbox failed for ${path.basename(filePath)}`);
        return null;
    }
}

try {
    firmwareData = JSON.parse(fsSync.readFileSync(path.join(PROJECT_ROOT, 'static/json/firmware/index.json'), 'utf8'));
    certIconsData = JSON.parse(fsSync.readFileSync(path.join(PROJECT_ROOT, 'static/json/certifications/icons.json'), 'utf8'));
    const pcData = loadDocusaurusJs(path.join(PROJECT_ROOT, 'static/json/product-categories/wisgate/rak7240v2/product-comparison/index.js'));
    const pcId = loadDocusaurusJs(path.join(PROJECT_ROOT, 'static/json/product-categories/wisgate/rak7240v2/product-comparison/identifier.js'));
    if (pcData) productComparisonData["RAK7240V2/RAK7240CV2"] = pcData;
    if (pcId) productComparisonIdentifiers["RAK7240V2/RAK7240CV2"] = pcId;
} catch (e) {
    console.warn("⚠️ Warning: Could not load some JSON data files.");
}

// --- 🪣 BUCKETS ---
const COMPONENTS_TO_DELETE = [
    'RkBottomNav', 'RkRedirect', 'RkExternalRedirect', 'NotificationContainer', 'GlobalDownloadIndicator',
    'NavigationBlocker', 'GoogleSchemaHead', 'GoogleTagManager', 'DocVersionBanner', 
    'DocVersionBadge', 'RkBreadcrumbs', 'RkDownloadModal', 'MeshtasticCTA', 'RkPopupBanner',
    'RkNewsletter', 'RkSearchV2', 'RkSearchHeader', 'DeveloperTools'
];

const COMPONENTS_TO_UNWRAP = [
    'RkProductBanner', 'RkProductCard', 'RkProductCardItem', 
    'RkProductCategory', 'WisgateOs2Card', 'TabNavigation', 'Tabs', 'TabItem', 
    'TabsList', 'TabsTrigger', 'TabsContent', 'RkHomePage', 'RkHomePageV2', 
    'RkProductCategoriesV2', 'RkProductCategoriesHeader', 'RkResourceAndPublication', 
    'RkSupportAndTroubleshooting', 'RkTopicCollections', 'Container', 'Grid', 'Flex'
];

const MDX_PARTIALS_MAP = {
    'BACnetGatewayConfiguration': 'LorawanNetworkServer/BACnetGatewayConfiguration/index.mdx',
    'WisDuoChirpstackAbp': 'LorawanNetworkServer/WisDuoChirpstackAbp/index.mdx',
    'WisDuoChirpstackOtaa': 'LorawanNetworkServer/WisDuoChirpstackOtaa/index.mdx',
    'WisDuoP2P': 'LorawanNetworkServer/WisDuoP2P/index.mdx',
    'WisDuoTtnAbp': 'LorawanNetworkServer/WisDuoTtnAbp/index.mdx',
    'WisDuoTtnOtaa': 'LorawanNetworkServer/WisDuoTtnOtaa/index.mdx',
    'SystemSettings': 'LorawanNetworkServer/SystemSettings/index.mdx',
    'WisGateGatewayDiagnostics': 'LorawanNetworkServer/WisGateGatewayDiagnostics/index.mdx',
    'WisGateGatewayExtensions': 'LorawanNetworkServer/WisGateGatewayExtensions/index.mdx',
    'WisGateOutdoorGatewayGatewayStatus': 'LorawanNetworkServer/WisGateOutdoorGatewayGatewayStatus/index.mdx',
    'WisGateIntegrationGuide': 'LorawanNetworkServer/WisGateGatewayIntegrationGuide/index.mdx',
    'WisGateOutdoorGatewayLoRaWANConfiguration': 'LorawanNetworkServer/WisGateOutdoorGatewayLoRaWANConfiguration/index.mdx',
    'WisgateGatewayNetworkInterface': 'LorawanNetworkServer/WisGateGatewayNetworkInterface/index.mdx',
    'WisGateGatewayRemoteManagement': 'LorawanNetworkServer/WisGateGatewayRemoteManagement/index.mdx',
    'WisGateGatewaySystemSettings': 'LorawanNetworkServer/WisGateGatewaySystemSettings/index.mdx',
    'WisGateIndoorGatewayGatewayStatus': 'LorawanNetworkServer/WisGateIndoorGatewayGatewayStatus/index.mdx',
    'WisGateGatewayIntegrationGuide': 'LorawanNetworkServer/WisGateGatewayIntegrationGuide/index.mdx',
    'WisGateIndoorGatewayLoRaWANConfiguration': 'LorawanNetworkServer/WisGateIndoorGatewayLoRaWANConfiguration/index.mdx',
    'TTNNode': 'LorawanNetworkServer/TTNNode/index.mdx',
    'ChirpStack': 'LorawanNetworkServer/ChirpStack/index.mdx',
    'TTN': 'LorawanNetworkServer/TTN/index.mdx'
};

// --- 🛠️ TABLE CLEANUP LOGIC ---

function decodeEntities(text) {
    const entities = {
        '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>',
        '&quot;': '"', '&#39;': "'", '&apos;': "'", '&#x2022;': '•'
    };
    return text.replace(/&(nbsp|amp|lt|gt|quot|#39|apos|#x2022);/gi, match => entities[match.toLowerCase()] || match);
}

function cleanCellText(text) {
    if (!text) return "";
    let t = text.replace(/<\/li>\s*<li[^>]*>/gi, " • ");
    t = t.replace(/<(ul|ol)[^>]*>\s*<li[^>]*>/gi, " • ");
    t = t.replace(/<\/li>\s*<\/(ul|ol)>/gi, "");
    t = t.replace(/<\/?(ul|ol|li)[^>]*>/gi, "");
    t = t.replace(/<br\s*\/?>/gi, " ");
    t = t.replace(/\n|\r/g, " ");

    t = decodeEntities(t);

    // Strip ALL remaining HTML tags inside the table cell
    t = t.replace(/<[^>]+>/g, " ");
    t = t.replace(/\s+/g, " ").trim();
    
    return t.replace(/(?<!\\)\|/g, "\\|");
}

function processTableGrid(grid) {
    if (grid.length < 2) return "";
    const maxCols = Math.max(...grid.map(row => row.length));
    
    // Forward Fill Columns 0 & 1
    for (let c = 0; c < Math.min(2, maxCols); c++) {
        let lastVal = "";
        for (let r = 0; r < grid.length; r++) {
            let cellVal = String(grid[r][c] || "").trim();
            if (!cellVal || cellVal.toLowerCase() === "none") {
                grid[r][c] = lastVal;
            } else {
                lastVal = cellVal;
            }
        }
    }

    const headerRow = grid[0].map(c => String(c || ""));
    const dataRows = grid.slice(1);
    
    const md = [`| ${headerRow.join(' | ')} |`, `| ${headerRow.map(() => '---').join(' | ')} |`];
    for (const row of dataRows) {
        const paddedRow = [...row];
        while (paddedRow.length < maxCols) paddedRow.push(""); 
        md.push(`| ${paddedRow.join(' | ')} |`);
    }

    return "\n\n" + md.join("\n") + "\n\n";
}

// 🚨 FIX: Replaced Regex table parsing with robust Cheerio DOM parsing
function htmlTableToMarkdown(htmlTable) {
    const $ = cheerio.load(htmlTable, null, false);
    const rows = [];
    
    $('tr').each((_, tr) => {
        const cells = [];
        $(tr).find('td, th').each((_, cell) => {
            const $cell = $(cell);
            const rowspan = parseInt($cell.attr('rowspan')) || 1;
            const colspan = parseInt($cell.attr('colspan')) || 1;
            
            // Extract HTML to preserve internal <br> and <li> before cleaning
            let text = cleanCellText($cell.html() || "");
            
            cells.push({ content: text, rowspan, colspan });
        });
        if (cells.length > 0) rows.push(cells);
    });

    if (rows.length === 0) return htmlTable;

    let maxCols = 0;
    rows.forEach(r => maxCols = Math.max(maxCols, r.reduce((sum, c) => sum + c.colspan, 0)));
    const grid = Array(rows.length).fill(null).map(() => Array(maxCols).fill(null));
    
    for (let r = 0; r < rows.length; r++) {
        let c = 0;
        for (const cell of rows[r]) {
            while (c < maxCols && grid[r][c] !== null) c++;
            if (c >= maxCols) break;
            
            for (let rs = 0; rs < cell.rowspan; rs++) {
                for (let cs = 0; cs < cell.colspan; cs++) {
                    if (r + rs < rows.length && c + cs < maxCols) {
                        grid[r + rs][c + cs] = cell.content;
                    }
                }
            }
            c += cell.colspan;
        }
    }
    return processTableGrid(grid);
}

function nativeMdTableFixer(mdTable) {
    const lines = mdTable.trim().split('\n').map(l => l.trim()).filter(l => l);
    const grid = [];
    for (const line of lines) {
        if (line.includes('---') && line.includes('|')) continue; 
        let cells = line.split(/(?<!\\)\|/).map(c => c.trim());
        if (cells.length > 0 && cells[0] === '') cells.shift();
        if (cells.length > 0 && cells[cells.length - 1] === '') cells.pop();
        if (cells.length > 0) grid.push(cells.map(c => cleanCellText(c)));
    }
    return processTableGrid(grid);
}

function htmlListToMarkdown(htmlList) {
    const $ = cheerio.load(htmlList, null, false);
    let md = '';
    function traverseList(node, depth) {
        const isOrdered = node.name === 'ol';
        let index = 1;
        $(node).children('li').each((_, li) => {
            const indent = '  '.repeat(depth);
            const prefix = isOrdered ? `${index++}. ` : '- ';
            const $liClone = $(li).clone();
            $liClone.children('ul, ol').remove();
            let text = $liClone.text().replace(/\s+/g, ' ').trim();
            md += `${indent}${prefix}${text}\n`;
            $(li).children('ul, ol').each((_, nested) => traverseList(nested, depth + 1));
        });
    }
    $.root().children('ul, ol').each((_, list) => traverseList(list, 0));
    return `\n${md}\n`;
}

// --- 🛠️ INJECTORS ---

function injectProductFilter(productLine) {
    const data = productComparisonData[productLine];
    const identifiers = productComparisonIdentifiers[productLine] || [];
    if (!data || identifiers.length === 0) return "";

    const keys = Object.keys(data);
    const grid = [ ["Feature", ...keys] ];

    identifiers.forEach(identifier => {
        const row = [identifier];
        keys.forEach(key => {
            let val = data[key]?.[identifier] || "—";
            if (Array.isArray(val)) val = val.join(', ');
            const $ = cheerio.load(String(val), null, false);
            row.push($.text().replace(/\s+/g, ' ').trim().replace(/(?<!\\)\|/g, "\\|"));
        });
        grid.push(row);
    });
    return processTableGrid(grid);
}

function injectFirmwareVersion(deviceStr) {
    for (const category in firmwareData) {
        for (const group of firmwareData[category] || []) {
            if (group.devices.includes(deviceStr)) return group.version;
        }
    }
    return "Unknown Version";
}

function injectCertIcons(propsString) {
    const keys = [];
    const regex = /"([a-zA-Z0-9_]+)"\s*:/g;
    let match;
    while ((match = regex.exec(propsString)) !== null) {
        keys.push(match[1].toLowerCase());
    }
    if (keys.length === 0) return "";

    let mdList = "\n### Certifications\n";
    keys.forEach(key => {
        const certName = certIconsData[key]?.name || key.toUpperCase();
        mdList += `- **${certName}**\n`;
    });
    return mdList + '\n';
}

// --- 🔄 MASTER TEXT PROCESSING LOGIC (ASYNC) ---
async function processMarkdownText(content, visitedPartials = new Set()) {
    content = content.replace(/^import\s+.*?from\s+['"].*?['"];?$/gm, '');
    content = content.replace(/Thank you for choosing.*?product\./gi, "");
    content = content.replace(/🎉/g, "");

    // 1. Inject MDX Partials
    for (const compName of Object.keys(MDX_PARTIALS_MAP)) {
        const regex = new RegExp(`<${compName}\\s*\\/?>|<${compName}>\\s*<\\/${compName}>`, 'g');
        if (regex.test(content)) {
            if (visitedPartials.has(compName)) {
                content = content.replace(regex, ''); 
                continue;
            }
            const newVisited = new Set(visitedPartials).add(compName);
            const partialPath = path.join(PROJECT_ROOT, 'docs', MDX_PARTIALS_MAP[compName]);
            
            if (fsSync.existsSync(partialPath)) {
                let partialContent = await fs.readFile(partialPath, 'utf8');
                partialContent = partialContent.replace(/^---[\s\S]*?---\n/, '');
                partialContent = await processMarkdownText(partialContent, newVisited);
                content = content.replace(regex, `\n${partialContent}\n`);
            }
        }
    }

    // 2. 🛡️ PROTECT CODE BLOCKS
    // 🚨 FIX: More robust regex to capture all code blocks (even indented ones or ones with props like c{8})
    const codeBlocks = new Map();
    content = content.replace(/(```[\s\S]*?```)|(`[^`\n]+`)/g, (match) => {
        const id = `__CODE_${crypto.randomUUID().replace(/-/g, '')}__`;
        codeBlocks.set(id, match);
        return id;
    });

    // 3. Anchor Tags
    content = content.replace(/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi, (match, href, inner) => {
        const cleanInner = inner.replace(/<[^>]+>/g, '').trim();
        return `[${cleanInner}](${href})`;
    });

    // 4. Delete Useless Components
    COMPONENTS_TO_DELETE.forEach(comp => {
        const regex = new RegExp(`<${comp}\\b[^>]*\\/?>|<${comp}\\b[^>]*>[\\s\\S]*?<\\/${comp}>`, 'g');
        content = content.replace(regex, '');
    });

    // 5. Unwrap UI Components
    COMPONENTS_TO_UNWRAP.forEach(comp => {
        const openRegex = new RegExp(`<${comp}\\b[^>]*>`, 'g');
        const closeRegex = new RegExp(`<\\/${comp}>`, 'g');
        content = content.replace(openRegex, '\n\n');
        content = content.replace(closeRegex, '\n\n');
    });

    // 6. Replace Images & Dividers
    content = content.replace(/<RkImage[\s\S]*?\/>/g, (match) => {
        const captionMatch = match.match(/caption=["']([^"']+)["']/);
        return `\n**Image:** ${captionMatch ? captionMatch[1] : 'Image'}\n`; 
    });
    content = content.replace(/<img\b[^>]*alt=["']([^"']*)["'][^>]*\/?>/gi, '\n**Image:** $1\n');
    content = content.replace(/<img\b[^>]*\/?>/gi, '\n**Image:**\n');
    content = content.replace(/<RkDivider[\s\S]*?\/>/g, '\n---\n');

    // 7. Data Injectors
    content = content.replace(/<RkProductFilter(?:\s+productLine=["']([^"']+)["'])?[\s\S]*?\/>/g, (m, pl) => injectProductFilter(pl || "RAK7240V2/RAK7240CV2"));
    content = content.replace(/<FirmwareVersion\s+device=["']([^"']+)["'][\s\S]*?\/>/g, (m, device) => injectFirmwareVersion(device));
    content = content.replace(/<RkCertificationIcons\s+certifications=\{([^}]+)\}[\s\S]*?\/>/g, (m, props) => injectCertIcons(props));

    // 8. 🚨 FIX: Strip details, summary, and explicit text
    content = content.replace(/<\/?(details|summary)\b[^>]*>/gi, ""); 
    content = content.replace(/Click to view the code/gi, "");

    // 9. Lists
    content = content.replace(/<(ul|ol)\b[^>]*>[\s\S]*?<\/\1>/gi, match => htmlListToMarkdown(match));

    // 10. 🚨 FIX: HTML Tables (More robust regex matching)
    content = content.replace(/<table\b[^>]*>[\s\S]*?<\/table>/gi, match => htmlTableToMarkdown(match));
    
    const mdTablePattern = /((?:^[ \t]*\|[^\n]+\|[ \t]*(?:\r?\n|$))+)/gm;
    content = content.replace(mdTablePattern, match => nativeMdTableFixer(match));

    // 11. Generic HTML Cleanups
    content = content.replace(/<br\s*\/?>/gi, "\n");
    content = content.replace(/<\/?(div|section|article|header|footer|figure|figcaption)[^>]*>/gi, "\n\n");
    content = content.replace(/<\/?(span|p|center|strong|b|em|i)[^>]*>/gi, " ");

    content = content.replace(/:::([a-z]+)\s*(.*)/g, (match, type, title) => `\n> **${title ? title.trim() : type.toUpperCase()}:**`);
    content = content.replace(/:::/g, ''); 

    // 12. Entities Decode
    content = decodeEntities(content);

    // 13. 🛡️ RESTORE CODE BLOCKS
    codeBlocks.forEach((val, id) => {
        content = content.replace(id, val);
    });

    // 14. Final spacing
    content = content.replace(/\n{3,}/g, '\n\n').trim();

    return content;
}

// --- 🧵 ASYNC CONCURRENCY POOL ---
async function asyncPool(concurrency, iterable, iteratorFn) {
    const ret = [];
    const executing = new Set();
    for (const item of iterable) {
        const p = Promise.resolve().then(() => iteratorFn(item));
        ret.push(p);
        executing.add(p);
        const clean = () => executing.delete(p);
        p.then(clean).catch(clean);
        if (executing.size >= concurrency) await Promise.race(executing);
    }
    return Promise.all(ret);
}

// --- 🏃 DIRECTORY CRAWLER ---
async function gatherFiles(dir, fileList = []) {
    let files;
    try { files = await fs.readdir(dir, { withFileTypes: true }); } 
    catch (e) { return fileList; }
    
    for (const file of files) {
        const fullPath = path.join(dir, file.name);
        if (file.isDirectory()) {
            await gatherFiles(fullPath, fileList);
        } else if (file.name.endsWith('.md') || file.name.endsWith('.mdx')) {
            fileList.push(fullPath);
        }
    }
    return fileList;
}

// --- 🚀 EXECUTE ---
async function main() {
    console.log(`\n========================================`);
    console.log(`🚀 Elite Asynchronous RAG Pre-processor`);
    console.log(`========================================\n`);

    if (fsSync.existsSync(OUTPUT_DIR)) {
        fsSync.rmSync(OUTPUT_DIR, { recursive: true, force: true });
    }
    fsSync.mkdirSync(OUTPUT_DIR, { recursive: true });

    const allFiles = await gatherFiles(TARGET_DIR);
    console.log(`📂 Found ${allFiles.length} documentation files.\n`);

    await asyncPool(15, allFiles, async (fullPath) => {
        try {
            const relativePath = path.relative(TARGET_DIR, fullPath);
            const outputPath = path.join(OUTPUT_DIR, relativePath);
            
            let cleanedMarkdown = await fs.readFile(fullPath, 'utf8');
            cleanedMarkdown = await processMarkdownText(cleanedMarkdown);

            const bodyContent = cleanedMarkdown.replace(/^---[\s\S]*?---\n/, '').trim();
            if (bodyContent.length === 0) {
                console.log(`⏭️  Skipping empty/redirect file: ${relativePath}`);
                return; 
            }

            await fs.mkdir(path.dirname(outputPath), { recursive: true });
            await fs.writeFile(outputPath.replace(/\.mdx$/, '.md'), cleanedMarkdown, 'utf8');
            console.log(`✅ Processed: ${relativePath}`);
            
        } catch (err) {
            console.error(`❌ Error processing ${fullPath}:`, err.message);
        }
    });

    console.log(`\n🎉 Success! Fully flattened, cleaned markdown is in: ${OUTPUT_DIR}\n`);
}

main();