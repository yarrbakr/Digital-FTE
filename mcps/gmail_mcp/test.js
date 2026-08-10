/**
 * Gmail MCP Standalone Test
 * Tests email sending without MCP protocol
 */

import { GmailAutomation } from './gmail.js';
import dotenv from 'dotenv';

dotenv.config();

async function test() {
    console.log('='.repeat(60));
    console.log('GMAIL MCP STANDALONE TEST');
    console.log('='.repeat(60));

    const gmail = new GmailAutomation();

    try {
        console.log('\nTest 1: Authentication');
        const connection = await gmail.testConnection();
        console.log('✅ Authentication successful');
        console.log('Connected as:', connection.email);

        console.log('\nTest 2: Send email');

        const recipient = process.env.TEST_EMAIL || 'your-email@example.com';
        console.log(`Recipient: ${recipient}`);
        console.log(
            'Note: Set TEST_EMAIL environment variable to customize recipient'
        );

        const result = await gmail.sendEmail(
            recipient,
            `Gmail MCP Test - ${new Date().toISOString()}`,
            `This is a test email from the custom Gmail MCP.

If you received this, the Gmail MCP is working correctly!

Sent from: AI Employee Silver Tier
Test timestamp: ${new Date().toISOString()}

Technical details:
- Using Gmail API v1
- Custom MCP server implementation
- Reusing Bronze tier credentials

---
Automated test - AI Employee Project`
        );

        console.log('✅ Email sent successfully');
        console.log('Result:', JSON.stringify(result, null, 2));

        console.log('\n' + '='.repeat(60));
        console.log('ALL TESTS PASSED');
        console.log('='.repeat(60));
        console.log('\nCheck your inbox to confirm email delivery.');
    } catch (error) {
        console.error('\n❌ TEST FAILED');
        console.error('Error:', error.message);
        console.error('\nCommon issues:');
        console.error('- Credentials file not found or invalid path');
        console.error('- OAuth tokens expired (re-run Bronze tier Gmail setup)');
        console.error('- Gmail API not enabled in Google Cloud Console');
        console.error('- Insufficient permissions/scopes');
        process.exit(1);
    }
}

test();