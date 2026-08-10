/**
 * Gmail Automation Class
 * Handles Gmail API authentication and email sending
 */

import { google } from 'googleapis';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export class GmailAutomation {
    constructor() {
        this.gmail = null;
        this.auth = null;
        console.error('[Gmail] Automation initialized');
    }

    /**
     * Authenticate with Gmail API
     */
    async authenticate() {
        if (this.auth) {
            return; // Already authenticated
        }

        console.error('[Gmail] Authenticating...');

        // Get credentials path from environment or default
        const credentialsPath =
            process.env.GMAIL_CREDENTIALS_PATH ||
            path.join(__dirname, '../../credentials.json');

        if (!fs.existsSync(credentialsPath)) {
            throw new Error(`Credentials file not found: ${credentialsPath}`);
        }

        // Load client credentials (nested under "installed" key)
        const credentials = JSON.parse(fs.readFileSync(credentialsPath, 'utf8'));
        const clientCreds = credentials.installed || credentials;

        // Load OAuth tokens from token.json
        const tokenPath =
            process.env.GMAIL_TOKEN_PATH ||
            path.join(__dirname, '../../token.json');

        if (!fs.existsSync(tokenPath)) {
            throw new Error(`Token file not found: ${tokenPath}. Run the OAuth flow first.`);
        }

        const token = JSON.parse(fs.readFileSync(tokenPath, 'utf8'));

        // Create OAuth2 client
        this.auth = new google.auth.OAuth2(
            clientCreds.client_id,
            clientCreds.client_secret,
            clientCreds.redirect_uris ? clientCreds.redirect_uris[0] : 'urn:ietf:wg:oauth:2.0:oob'
        );

        // Set credentials from token file
        this.auth.setCredentials({
            access_token: token.token,
            refresh_token: token.refresh_token,
            token_type: token.token_type || 'Bearer',
            expiry_date: token.expiry ? new Date(token.expiry).getTime() : undefined,
        });

        // Create Gmail service
        this.gmail = google.gmail({ version: 'v1', auth: this.auth });

        console.error('[Gmail] Authentication successful');
    }

    /**
     * Send an email via Gmail
     */
    async sendEmail(to, subject, body) {
        try {
            // Ensure authenticated
            await this.authenticate();

            console.error(`[Gmail] Composing email to: ${to}`);

            // Create email in RFC 2822 format
            const email = [
                `To: ${to}`,
                `Subject: ${subject}`,
                'Content-Type: text/plain; charset=utf-8',
                '',
                body,
            ].join('\n');

            // Encode email in base64url format
            const encodedEmail = Buffer.from(email)
                .toString('base64')
                .replace(/\+/g, '-')
                .replace(/\//g, '_')
                .replace(/=+$/, '');

            // Send email
            const result = await this.gmail.users.messages.send({
                userId: 'me',
                requestBody: {
                    raw: encodedEmail,
                },
            });

            console.error('[Gmail] Email sent successfully');

            return {
                success: true,
                messageId: result.data.id,
                to: to,
                subject: subject,
                timestamp: new Date().toISOString(),
                message: 'Email sent successfully via Gmail API',
            };
        } catch (error) {
            console.error(`[Gmail] Send failed: ${error.message}`);

            // Check if it's a token refresh error
            if (error.code === 401 || error.message.includes('invalid_grant')) {
                throw new Error(
                    'Gmail authentication expired. Please re-authenticate using Bronze tier Gmail setup.'
                );
            }

            throw new Error(`Failed to send email: ${error.message}`);
        }
    }

    /**
     * Test connection to Gmail API
     */
    async testConnection() {
        await this.authenticate();

        // Get profile to verify connection
        const profile = await this.gmail.users.getProfile({ userId: 'me' });

        return {
            success: true,
            email: profile.data.emailAddress,
            messagesTotal: profile.data.messagesTotal,
        };
    }
}