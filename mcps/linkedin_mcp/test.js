/**
 * Test LinkedIn MCP
 */

import { LinkedInAutomation } from './linkedin.js';
import dotenv from 'dotenv';

dotenv.config();

async function test() {
    console.log('=== LinkedIn MCP Test ===\n');

    const linkedin = new LinkedInAutomation();

    try {
        const testPost = `Testing my custom LinkedIn MCP! 🚀

Built with Playwright for AI Employee hackathon.

#AI #Automation #BuildingInPublic

(Test - ${new Date().toISOString()})`;

        const result = await linkedin.createPost(testPost);

        console.log('✅ SUCCESS!');
        console.log(JSON.stringify(result, null, 2));
    } catch (error) {
        console.error('❌ FAILED:', error.message);
        process.exit(1);
    } finally {
        await linkedin.close();
    }
}

test();