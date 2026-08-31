/**
 * LinkedIn Automation Class
 * Core posting logic with Playwright
 */

import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.join(__dirname, '../../.env') });

export class LinkedInAutomation {
    constructor() {
        this.context = null;
        this.page = null;
        this.isLoggedIn = false;
        this.sessionDir = './.linkedin-session';
    }

    async initialize() {
        if (this.context) return;

        this.context = await chromium.launchPersistentContext(this.sessionDir, {
            headless: false,
            args: ['--no-sandbox', '--disable-setuid-sandbox'],
        });

        this.page = this.context.pages()[0] || (await this.context.newPage());
    }

    async randomDelay(min = 1000, max = 3000) {
        await new Promise((r) => setTimeout(r, Math.random() * (max - min) + min));
    }

    async login() {
        if (this.isLoggedIn) return;

        await this.initialize();
        await this.page.goto('https://www.linkedin.com/feed/');
        await this.randomDelay(2000, 4000);

        if (this.page.url().includes('/feed/')) {
            console.error('[LinkedIn] Session restored');
            this.isLoggedIn = true;
            return;
        }

        await this.performLogin();
    }

    async performLogin() {
        const email = process.env.LINKEDIN_EMAIL;
        const password = process.env.LINKEDIN_PASSWORD;

        if (!email || !password) {
            throw new Error('LinkedIn credentials missing');
        }

        await this.page.goto('https://www.linkedin.com/login');
        await this.randomDelay(1000, 2000);
        await this.page.fill('#username', email);
        await this.randomDelay(500, 1000);
        await this.page.fill('#password', password);
        await this.randomDelay(500, 1000);
        await this.page.click('button[type="submit"]');

        try {
            await this.page.waitForURL('**/feed/**', { timeout: 30000 });
            this.isLoggedIn = true;
        } catch (error) {
            if ((await this.page.content()).includes('captcha')) {
                throw new Error('CAPTCHA detected. Solve manually.');
            }
            throw new Error('Login failed');
        }
    }

    async createPost(content, retryCount = 0) {
        try {
            await this.login();

            if (!this.page.url().includes('/feed/')) {
                await this.page.goto('https://www.linkedin.com/feed/');
                await this.randomDelay(2000, 3000);
            }

            const selectors = [
                'button[aria-label*="Start a post"]',
                'button:has-text("Start a post")',
            ];

            let clicked = false;
            for (const sel of selectors) {
                try {
                    await this.page.click(sel, { timeout: 5000 });
                    clicked = true;
                    break;
                } catch (e) {
                    continue;
                }
            }

            if (!clicked) throw new Error('Start post button not found');

            await this.randomDelay(1000, 2000);
            await this.page.waitForSelector('.ql-editor, [role="textbox"]', {
                timeout: 10000,
            });
            await this.randomDelay(500, 1000);

            const editorSelectors = ['.ql-editor', '[role="textbox"]'];
            let typed = false;
            for (const sel of editorSelectors) {
                try {
                    await this.page.fill(sel, content);
                    typed = true;
                    break;
                } catch (e) {
                    continue;
                }
            }

            if (!typed) throw new Error('Editor not found');

            await this.randomDelay(1500, 2500);

            const postSelectors = [
                'button[aria-label="Post"]',
                'button:has-text("Post")',
            ];

            let posted = false;
            for (const sel of postSelectors) {
                try {
                    await this.page.click(sel, { timeout: 5000 });
                    posted = true;
                    break;
                } catch (e) {
                    continue;
                }
            }

            if (!posted) throw new Error('Post button not found');

            await this.randomDelay(3000, 5000);

            // VERIFY: Navigate to feed and confirm post actually published
            console.error('[LinkedIn] Verifying post...');
            await this.page.goto('https://www.linkedin.com/feed/');
            await this.randomDelay(2000, 3000);

            const searchText = content.substring(0, 50);
            const feedContent = await this.page.content();
            const postVerified = feedContent.includes(searchText);

            if (!postVerified) {
                console.error('[LinkedIn] Post not found in feed after publishing');
                console.error(`[LinkedIn] Searched for: "${searchText}"`);
                throw new Error('Post not found in feed after publishing - possible silent failure');
            }

            console.error('[LinkedIn] ✅ Post verified in feed');

            return {
                success: true,
                verified: true,
                timestamp: new Date().toISOString(),
                content: content,
            };
        } catch (error) {
            if (retryCount < 3) {
                console.error(`[LinkedIn] Retry ${retryCount + 1}/3`);
                this.isLoggedIn = false;
                await this.randomDelay(5000, 10000);
                return this.createPost(content, retryCount + 1);
            }
            throw error;
        }
    }

    async close() {
        if (this.context) {
            await this.context.close();
            this.context = null;
            this.isLoggedIn = false;
        }
    }
}